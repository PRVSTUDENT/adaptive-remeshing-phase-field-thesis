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
            self.assertGreater(idx_gen, idx_val, "generate_missing_evidence_report.py must be invoked AFTER validate_f40_runtime_audits.py")

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
            "repository_inventory", "repository_resolution", "geometry_conversion_observation",
            "usable_geometry_validation", "element_type_assignment", "mesh_control_assignment", "mesh_generation",
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
            self.assertEqual(res.returncode, 0, "Validator failed on valid schema and 21 passing phases: " + res.stdout + res.stderr)
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

    def test_matrix_validators_share_identical_phase_contract(self):
        import importlib.util
        v38_path = os.path.join(self.pkg_dir, "runtime", "validate_f38_matrix_results.py")
        v40_path = os.path.join(self.pkg_dir, "runtime", "validate_f40_runtime_audits.py")

        spec38 = importlib.util.spec_from_file_location("validate_f38_matrix_results", v38_path)
        mod38 = importlib.util.module_from_spec(spec38)
        spec38.loader.exec_module(mod38)

        spec40 = importlib.util.spec_from_file_location("validate_f40_runtime_audits", v40_path)
        mod40 = importlib.util.module_from_spec(spec40)
        spec40.loader.exec_module(mod40)

        self.assertEqual(
            mod38.EXPECTED_F38_PHASES,
            mod40.EXPECTED_F38_PHASES,
            "validate_f38_matrix_results and validate_f40_runtime_audits must define identical EXPECTED_F38_PHASES lists"
        )
        self.assertEqual(len(mod40.EXPECTED_F38_PHASES), 21, "EXPECTED_F38_PHASES must contain exactly 21 phases")

    def test_pbs_script_rejects_direct_execution_without_wrapper_guard(self):
        import subprocess
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        env = os.environ.copy()
        env.pop("F40_GUARDED_WRAPPER_INVOKED", None)
        proc = subprocess.run(["bash", pbs_path], capture_output=True, text=True, env=env)
        self.assertNotEqual(proc.returncode, 0, "Direct execution of M2RMBISECT1.pbs must fail")
        self.assertIn("FATAL: Direct execution of M2RMBISECT1.pbs is prohibited", proc.stderr)

    def test_pbs_script_rejects_missing_pbs_provenance(self):
        import subprocess
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        env = os.environ.copy()
        env["F40_GUARDED_WRAPPER_INVOKED"] = "1"
        env.pop("PBS_JOBID", None)
        env.pop("PBS_NODEFILE", None)
        proc = subprocess.run(["bash", pbs_path], capture_output=True, text=True, env=env)
        self.assertNotEqual(proc.returncode, 0, "Execution without genuine PBS batch provenance must fail")
        self.assertIn("FATAL: Genuine PBS batch provenance required", proc.stderr)

    def test_pbs_script_rejects_non_batch_environment(self):
        import subprocess, tempfile
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        env = os.environ.copy()
        env["F40_GUARDED_WRAPPER_INVOKED"] = "1"
        env["PBS_JOBID"] = "12345.testnode"
        env["PBS_ENVIRONMENT"] = "PBS_INTERACTIVE"
        env["PBS_O_HOST"] = "testhost"
        env["PBS_QUEUE"] = "entry_imfdfkmq"
        with tempfile.NamedTemporaryFile("w", delete=False) as nf:
            nf.write("othernode\n")
            nodefile_path = nf.name
        env["PBS_NODEFILE"] = nodefile_path
        try:
            proc = subprocess.run(["bash", pbs_path], capture_output=True, text=True, env=env)
            self.assertNotEqual(proc.returncode, 0, "Execution with non-PBS_BATCH environment must fail")
            self.assertIn("FATAL: Genuine PBS batch provenance required", proc.stderr)
        finally:
            if os.path.exists(nodefile_path):
                os.remove(nodefile_path)

    def test_pbs_script_rejects_host_absent_from_nodefile(self):
        import subprocess, tempfile
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        env = os.environ.copy()
        env["F40_GUARDED_WRAPPER_INVOKED"] = "1"
        env["PBS_JOBID"] = "12345.testnode"
        env["PBS_ENVIRONMENT"] = "PBS_BATCH"
        env["PBS_O_HOST"] = "testhost"
        env["PBS_QUEUE"] = "entry_imfdfkmq"
        with tempfile.NamedTemporaryFile("w", delete=False) as nf:
            nf.write("unmatched_node_name\n")
            nodefile_path = nf.name
        env["PBS_NODEFILE"] = nodefile_path
        try:
            proc = subprocess.run(["bash", pbs_path], capture_output=True, text=True, env=env)
            self.assertNotEqual(proc.returncode, 0, "Execution with host absent from PBS_NODEFILE must fail")
            self.assertIn("FATAL: Current compute host is absent from PBS_NODEFILE", proc.stderr)
        finally:
            if os.path.exists(nodefile_path):
                os.remove(nodefile_path)

    def test_runtime_validator_rejects_missing_scheduler_provenance(self):
        import importlib.util, tempfile
        v40_path = os.path.join(self.pkg_dir, "runtime", "validate_f40_runtime_audits.py")
        spec = importlib.util.spec_from_file_location("validate_f40_runtime_audits", v40_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory missing SCHEDULER_PROVENANCE.json
            with open(os.path.join(tmpdir, "STATUS.json"), "w") as f:
                f.write("{}")
            sys.argv = ["validate_f40_runtime_audits.py", tmpdir]
            rc = mod.main()
            self.assertNotEqual(rc, 0, "Runtime validator must fail when SCHEDULER_PROVENANCE.json is missing")

    def test_wrapper_qstat_duplicate_detection_logic(self):
        import subprocess
        # Mock qstat output fixture with M2RMBISECT1 job in 2nd column after header
        fixture_qstat = "Job ID            Name             User             Time Use S Queue\n----------------- ---------------- ---------------- -------- - -----\n1384588.mmaster02 M2RMBISECT1      testuser         00:00:00 R entry_imfdfkmq\n"
        cmd = ["awk", "NR > 2 && $2 == \"M2RMBISECT1\" {found=1} END {exit !found}"]
        proc = subprocess.run(cmd, input=fixture_qstat, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, "Awk logic must detect M2RMBISECT1 job in qstat output fixture")

        # Mock qstat output fixture without M2RMBISECT1 job
        fixture_other = "Job ID            Name             User             Time Use S Queue\n----------------- ---------------- ---------------- -------- - -----\n1384589.mmaster02 OTHERJOB         testuser         00:00:00 R entry_imfdfkmq\n"
        proc2 = subprocess.run(cmd, input=fixture_other, text=True, capture_output=True)
        self.assertNotEqual(proc2.returncode, 0, "Awk logic must return non-zero when M2RMBISECT1 job is absent")

    def test_missing_evidence_report_returncode(self):
        import importlib.util, tempfile
        gen_path = os.path.join(self.pkg_dir, "runtime", "generate_missing_evidence_report.py")
        spec = importlib.util.spec_from_file_location("generate_missing_evidence_report", gen_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Missing files case -> exit 1
            sys.argv = ["generate_missing_evidence_report.py", tmpdir]
            rc_missing = mod.main()
            self.assertEqual(rc_missing, 1, "generate_missing_evidence_report must return 1 when expected files are missing")

            # Complete case -> exit 0
            for fname in mod.EXPECTED_EVIDENCE_FILES:
                with open(os.path.join(tmpdir, fname), "w") as f:
                    f.write("{}")
            rc_complete = mod.main()
            self.assertEqual(rc_complete, 0, "generate_missing_evidence_report must return 0 when all expected files exist")

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

            valid_hashes, status_msg, metrics = mod.verify_script_hashes(tmpdir)
            self.assertFalse(valid_hashes, "verify_script_hashes should return False on modified helper content")
            self.assertEqual(status_msg, "helper_hash_mismatch")
            self.assertFalse(metrics.get("helper_hash_matched", True))

    def test_usable_geometry_validation_fails_on_zero_faces(self):
        matrix_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f38_cae_diagnostic_matrix", matrix_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        class DummyPart:
            def __init__(self):
                self.faces = []
                self.vertices = []
                self.edges = [1, 2]

        ctx = {
            'geom_part': DummyPart(),
            'geometry_conversion_api_observation': {
                'face_count': 0,
                'vertex_count': 0,
                'is_wire_only': True
            }
        }
        with self.assertRaises(RuntimeError):
            mod.phase_usable_geometry_validation(ctx)

    def test_crack_mesh_topology_classification(self):
        matrix_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f38_cae_diagnostic_matrix", matrix_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        class DummyNode:
            def __init__(self, label, x, y):
                self.label = label
                self.coordinates = (x, y, 0.0)

        class DummyElem:
            def __init__(self, n1, n2):
                self.connectivity = (n1, n2)

        # Case A: 15 double-label pairs + 1 tip node -> duplicated_crack_face_nodes
        nodes_dups = [DummyNode(2, 0.0, 0.0)]
        lbl = 3
        for i in range(15):
            x = -0.5 + i * (0.5 / 15.0)
            nodes_dups.append(DummyNode(lbl, x, 0.0))
            nodes_dups.append(DummyNode(lbl + 1, x, 0.0))
            lbl += 2

        class DummyPartDups:
            def __init__(self):
                self.nodes = nodes_dups
                self.elements = [DummyElem(3, 5), DummyElem(4, 6)]

        ctx_dups = {'crack_geom_part': DummyPartDups()}
        res_dups = mod.phase_crack_mesh_topology(ctx_dups)
        self.assertEqual(res_dups['crack_mesh_classification'], 'duplicated_crack_face_nodes')
        self.assertEqual(res_dups['coincident_node_pairs_count'], 15)

        # Case B: 15 single-label nodes -> continuous_centerline_mesh
        nodes_single = []
        for i in range(16):
            x = -0.5 + i * (0.5 / 15.0)
            nodes_single.append(DummyNode(i + 1, x, 0.0))

        class DummyPartSingle:
            def __init__(self):
                self.nodes = nodes_single
                self.elements = [DummyElem(1, 2)]

        ctx_single = {'crack_geom_part': DummyPartSingle()}
        res_single = mod.phase_crack_mesh_topology(ctx_single)
        self.assertEqual(res_single['crack_mesh_classification'], 'continuous_centerline_mesh')

    def test_static_gate_validator_passes(self):
        res = subprocess.run([sys.executable, self.validator_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res.returncode, 0, "Static validator failed: " + res.stdout + res.stderr)

if __name__ == "__main__":
    unittest.main()
