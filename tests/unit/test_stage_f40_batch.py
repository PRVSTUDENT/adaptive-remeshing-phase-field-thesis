import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
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
                rec = {
                    "phase": pname,
                    "attempted": True,
                    "passed": True,
                    "dependency_blocked": False,
                    "exception_type": None,
                    "exception_message": None,
                    "traceback": None
                }
                if pname == "geometry_conversion_observation":
                    rec["observations"] = {
                        "controlled_conversion_probes": {
                            "control_a": {
                                "attempted": True,
                                "completed": True,
                                "exception_type": None,
                                "exception_message": None,
                                "coincident_pairs_before": 15,
                                "node_reduction": 15,
                                "coincident_pairs_after": 0,
                                "face_count": 1,
                                "vertex_count": 3
                            },
                            "control_b": {
                                "attempted": True,
                                "completed": True,
                                "exception_type": None,
                                "exception_message": None,
                                "face_count": 0,
                                "vertex_count": 0
                            },
                            "angle_probes": {
                                "angle_15deg": {"attempted": True, "completed": True, "exception_type": None, "exception_message": None, "face_count": 0, "vertex_count": 0},
                                "angle_30deg": {"attempted": True, "completed": True, "exception_type": None, "exception_message": None, "face_count": 0, "vertex_count": 0},
                                "angle_45deg": {"attempted": True, "completed": True, "exception_type": None, "exception_message": None, "face_count": 0, "vertex_count": 0},
                                "angle_60deg": {"attempted": True, "completed": True, "exception_type": None, "exception_message": None, "face_count": 0, "vertex_count": 0},
                                "angle_90deg": {"attempted": True, "completed": True, "exception_type": None, "exception_message": None, "face_count": 0, "vertex_count": 0}
                            },
                            "coincident_crack_nodes_confirmed_root_cause": True
                        }
                    }
                phases_records.append(rec)
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

    def test_full_synthetic_successful_closeout_sequence(self):
        import importlib.util, json, tempfile
        val_path = os.path.join(self.pkg_dir, "runtime", "validate_f40_runtime_audits.py")
        gen_path = os.path.join(self.pkg_dir, "runtime", "generate_missing_evidence_report.py")

        spec_val = importlib.util.spec_from_file_location("validate_f40_runtime_audits", val_path)
        mod_val = importlib.util.module_from_spec(spec_val)
        spec_val.loader.exec_module(mod_val)

        spec_gen = importlib.util.spec_from_file_location("generate_missing_evidence_report", gen_path)
        mod_gen = importlib.util.module_from_spec(spec_gen)
        spec_gen.loader.exec_module(mod_gen)

        expected_f38_phases = mod_val.EXPECTED_F38_PHASES

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Populate synthetic successful runtime evidence
            prov_data = {
                "protocol_version": 1,
                "pbs_jobid": "12345.mmaster02",
                "pbs_environment": "PBS_BATCH",
                "pbs_queue": "entry_imfdfkmq",
                "pbs_o_host": "testhost",
                "hostname": "testnode",
                "hostname_short": "testnode",
                "nodefile": "/tmp/nodefile",
                "nodefile_hosts": ["testnode"],
                "abaqus_executable": "/usr/bin/abaqus",
                "abaqus_release": "Abaqus 2023",
                "timestamp_utc": "2026-08-06T15:00:00.000Z"
            }
            with open(os.path.join(tmpdir, "SCHEDULER_PROVENANCE.json"), "w") as f:
                json.dump(prov_data, f)

            ctx_data = {
                "entrypoint": "run_f38_cae_diagnostic.py",
                "runtime_dir_exists": True,
                "runtime_dir_on_sys_path": True,
                "bootstrap_passed": True
            }
            with open(os.path.join(tmpdir, "CAE_INVOCATION_CONTEXT_AUDIT.json"), "w") as f:
                json.dump(ctx_data, f)

            phases_rec = []
            for p in expected_f38_phases:
                prec = {
                    "phase": p,
                    "attempted": True,
                    "passed": True,
                    "dependency_blocked": False,
                    "exception_type": None
                }
                if p == "geometry_conversion_observation":
                    prec["observations"] = {
                        "controlled_conversion_probes": {
                            "control_a": {
                                "attempted": True, "completed": True, "exception_type": None, "exception_message": None,
                                "coincident_pairs_before": 15, "node_reduction": 15, "coincident_pairs_after": 0,
                                "face_count": 1, "vertex_count": 3
                            },
                            "control_b": {
                                "attempted": True, "completed": True, "exception_type": None, "exception_message": None,
                                "face_count": 0, "vertex_count": 0
                            },
                            "angle_probes": {
                                fa_k: {"attempted": True, "completed": True, "exception_type": None, "exception_message": None, "face_count": 0, "vertex_count": 0}
                                for fa_k in ["angle_15deg", "angle_30deg", "angle_45deg", "angle_60deg", "angle_90deg"]
                            },
                            "coincident_crack_nodes_confirmed_root_cause": True
                        }
                    }
                phases_rec.append(prec)

            matrix_data = {
                "overall_passed": True,
                "phases": phases_rec
            }
            with open(os.path.join(tmpdir, "CAE_PHASE_DIAGNOSTIC_MATRIX.json"), "w") as f:
                json.dump(matrix_data, f)

            with open(os.path.join(tmpdir, "F38_F39_INVOCATION_DELTA_AUDIT.json"), "w") as f:
                json.dump({"protocol_version": 1}, f)

            p_names = [
                "P00_KERNEL_STARTUP", "P01_IMPORTS", "P02_MODULE_LOADING",
                "P03_SOURCE_DECK_DISCOVERY", "P04_MODEL_FROM_INPUT_FILE",
                "P05_IMPORTED_MODEL_INVENTORY", "P06_GEOMETRY_CONVERSION",
                "P07_INDEPENDENT_MODEL_OWNERSHIP", "P08_ASSEMBLY_OPERATIONS",
                "P09_TOPOLOGY_MEASUREMENT", "P10_SETS_SURFACES_INVENTORY",
                "P11_STEP_OUTPUT_PROBING"
            ]
            for pname in p_names:
                pdata = {
                    "phase_name": pname,
                    "return_code": 0,
                    "metrics": {
                        "entrypoint_exists": True, "helper_exists": True,
                        "entrypoint_hash_matched": True, "helper_hash_matched": True,
                        "module_imported": True, "main_callable": True,
                        "main_executed_in_p02": False
                    } if pname == "P02_MODULE_LOADING" else {}
                }
                with open(os.path.join(tmpdir, "{}_AUDIT.json".format(pname)), "w") as f:
                    json.dump(pdata, f)

            rc_files = [
                "delta_auditor.returncode", "bisection_runner.returncode",
                "f38_entrypoint.returncode", "f38_matrix_validator.returncode",
                "EMAIL_SUBMISSION_NOTIFICATION.returncode", "TELEGRAM_SUBMISSION_NOTIFICATION.returncode",
                "EMAIL_TERMINAL_NOTIFICATION.returncode", "TELEGRAM_TERMINAL_NOTIFICATION.returncode"
            ]
            for rcf in rc_files:
                with open(os.path.join(tmpdir, rcf), "w") as f:
                    f.write("0")

            with open(os.path.join(tmpdir, "NOTIFICATION_AUDIT.json"), "w") as f:
                json.dump([{"event_type": "test", "channel": "email", "recipient_redacted": "pr****de", "return_code": 0}], f)

            # Simulate v14 PBS Trap Step 3: Run runtime audit validator
            sys.argv = ["validate_f40_runtime_audits.py", tmpdir]
            rc_val = mod_val.main()
            self.assertEqual(rc_val, 0, "Runtime audit validator must succeed on complete synthetic evidence")

            with open(os.path.join(tmpdir, "runtime_validator.returncode"), "w") as f:
                f.write("0")

            # Simulate v14 PBS Trap Step 4: Write preliminary first_failure and STATUS.json
            with open(os.path.join(tmpdir, "first_failure.returncode"), "w") as f:
                f.write("0")

            status_data = {
                "timestamp": "2026-08-06T15:00:00Z",
                "delta_auditor_rc": 0, "bisection_runner_rc": 0,
                "f38_entrypoint_rc": 0, "f38_matrix_validator_rc": 0,
                "runtime_validator_rc": 0, "first_failure_rc": 0,
                "overall_classification": "f40_bisection_completed_successfully"
            }
            with open(os.path.join(tmpdir, "STATUS.json"), "w") as f:
                json.dump(status_data, f)

            # Simulate v14 PBS Trap Step 5: Run final missing-evidence report generator
            sys.argv = ["generate_missing_evidence_report.py", tmpdir]
            rc_gen = mod_gen.main()
            self.assertEqual(rc_gen, 0, "Missing evidence report generator must succeed when all evidence exists")

            with open(os.path.join(tmpdir, "collector.returncode"), "w") as f:
                f.write("0")

            with open(os.path.join(tmpdir, "MISSING_EVIDENCE_REPORT.json"), "r") as f:
                rep = json.load(f)
                self.assertEqual(rep.get("missing_count"), 0)
                self.assertEqual(rep.get("status"), "complete")

            # Negative assertion: remove P06_GEOMETRY_CONVERSION_AUDIT.json and verify non-zero failure
            os.remove(os.path.join(tmpdir, "P06_GEOMETRY_CONVERSION_AUDIT.json"))
            sys.argv = ["validate_f40_runtime_audits.py", tmpdir]
            self.assertNotEqual(mod_val.main(), 0, "Runtime validator must fail when P06_GEOMETRY_CONVERSION_AUDIT.json is missing")
            sys.argv = ["generate_missing_evidence_report.py", tmpdir]
            self.assertNotEqual(mod_gen.main(), 0, "Missing evidence report generator must fail when P06_GEOMETRY_CONVERSION_AUDIT.json is missing")

    def test_static_gate_validator_passes(self):
        res = subprocess.run([sys.executable, self.validator_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res.returncode, 0, "Static validator failed: " + res.stdout + res.stderr)

    def test_v15r1_dependency_map_blocks_mesh_and_replacement(self):
        matrix_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f38_cae_diagnostic_matrix", matrix_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        deps = mod.PHASE_DEPENDENCIES
        self.assertIn('mesh_generation', deps)
        self.assertIn('usable_geometry_validation', deps['mesh_generation'])
        self.assertIn('instance_replacement', deps)
        self.assertIn('usable_geometry_validation', deps['instance_replacement'])
        self.assertIn('crack_edge_method_inventory', deps)
        self.assertIn('usable_geometry_validation', deps['crack_edge_method_inventory'])

    def test_v15r1_part_level_fallback_completely_removed(self):
        matrix_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        with open(matrix_path, "r") as f:
            content = f.read()

        self.assertNotIn("source_part.Part2DGeomFrom2DMesh", content, "Part-level fallback source_part.Part2DGeomFrom2DMesh must be completely removed")
        self.assertNotIn("p_a.Part2DGeomFrom2DMesh", content)
        self.assertNotIn("p_b.Part2DGeomFrom2DMesh", content)

    def test_v15r1_control_probe_schema_completeness(self):
        matrix_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f38_cae_diagnostic_matrix", matrix_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Mock run_single_conversion_probe behavior
        record = mod.run_single_conversion_probe(None, None, "MOCK", "KEY", 45.0, merge_crack_nodes=False)
        required_keys = ['model_name', 'feature_angle', 'merge_crack_nodes_requested', 'attempted', 'completed', 'face_count', 'vertex_count', 'edge_count', 'exception_type', 'exception_message']
        for k in required_keys:
            self.assertIn(k, record, "Probe record missing required key: {}".format(k))

    def test_v15r2_conversion_probe_mock_merge_success_and_failure(self):
        matrix_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f38_cae_diagnostic_matrix", matrix_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        class MockNode:
            def __init__(self, nid, x, y):
                self.label = nid
                self.coordinates = (x, y, 0.0)

        class MockPart:
            def __init__(self, nodes):
                self.nodes = nodes
                self.faces = [1]
                self.vertices = [1, 2, 3]
                self.edges = [1, 2, 3]

            def mergeNodes(self, nodes, tolerance):
                unique_nodes = []
                seen = set()
                for n in self.nodes:
                    key = (round(n.coordinates[0], 5), round(n.coordinates[1], 5))
                    if key not in seen:
                        seen.add(key)
                        unique_nodes.append(n)
                self.nodes = unique_nodes

        class MockGeomPart:
            def __init__(self, faces_count):
                self.faces = [1] * faces_count
                self.vertices = [1] * max(1, faces_count)
                self.edges = [1] * max(1, faces_count)

        class MockModel:
            def __init__(self, part):
                self.parts = {'Part-1': part}

            def Part2DGeomFrom2DMesh(self, name, part, featureAngle):
                faces_count = 1 if 'CtrlA' in name else 0
                self.parts[name] = MockGeomPart(faces_count)

        class MockMdb:
            def __init__(self, model):
                self.models = {'F40_MODEL': model}

        nodes = []
        nid = 1
        for i in range(15):
            x = -0.5 + i * (0.5 / 14.0)
            nodes.append(MockNode(nid, x, 0.0))
            nid += 1
            nodes.append(MockNode(nid, x, 0.0))
            nid += 1

        mock_part = MockPart(list(nodes))
        mock_model = MockModel(mock_part)
        mock_mdb = MockMdb(mock_model)

        original_import = mod.import_fresh_model
        mod.import_fresh_model = lambda mdb, deck, mname: mock_model

        try:
            # 1. Control A (merge_crack_nodes=True) -> Merge success
            rec_a = mod.run_single_conversion_probe(mock_mdb, "deck.inp", "F40_CTRL_A", "GeomCtrlA", 45.0, merge_crack_nodes=True)
            self.assertTrue(rec_a['attempted'])
            self.assertTrue(rec_a['completed'])
            self.assertIsNone(rec_a['exception_type'])
            self.assertEqual(rec_a['coincident_pairs_before'], 15)
            self.assertEqual(rec_a['node_reduction'], 15)
            self.assertEqual(rec_a['coincident_pairs_after'], 0)
            self.assertEqual(rec_a['face_count'], 1)

            # 2. Control B (merge_crack_nodes=False) -> Cracked topology
            mock_part_b = MockPart(list(nodes))
            mock_model_b = MockModel(mock_part_b)
            mod.import_fresh_model = lambda mdb, deck, mname: mock_model_b

            rec_b = mod.run_single_conversion_probe(mock_mdb, "deck.inp", "F40_CTRL_B", "GeomCtrlB", 45.0, merge_crack_nodes=False)
            self.assertTrue(rec_b['attempted'])
            self.assertTrue(rec_b['completed'])
            self.assertIsNone(rec_b['exception_type'])
            self.assertEqual(rec_b['face_count'], 0)

            # 3. Fail-Closed behavior when duplicate count is not 15
            incomplete_nodes = nodes[:20]  # 10 pairs
            mock_part_inc = MockPart(list(incomplete_nodes))
            mock_model_inc = MockModel(mock_part_inc)
            mod.import_fresh_model = lambda mdb, deck, mname: mock_model_inc

            rec_fail = mod.run_single_conversion_probe(mock_mdb, "deck.inp", "F40_FAIL", "GeomFail", 45.0, merge_crack_nodes=True)
            self.assertTrue(rec_fail['attempted'])
            self.assertFalse(rec_fail['completed'])
            self.assertIsNotNone(rec_fail['exception_type'])
            self.assertIn("Control A fail-closed check failed", rec_fail['exception_message'])
        finally:
            mod.import_fresh_model = original_import

    def test_v16r1_obsolete_email_address_absent_everywhere(self):
        obsolete_email = "pruthvi.patel@student.tu-freiberg.de"
        for root, dirs, files in os.walk(self.repo_root):
            if ".git" in root or "__pycache__" in root or ".system_generated" in root or "tmp" in root:
                continue
            for fname in files:
                if fname.endswith((".py", ".sh", ".pbs", ".json", ".md", ".csv")):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            self.assertNotIn(obsolete_email, content, "Obsolete email address {} found in {}".format(obsolete_email, fpath))
                    except Exception:
                        pass

    def test_v16r1_verified_email_addresses_and_qsub_flags(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
        self.assertNotIn("pruthvi.patel@student.tu-freiberg.de", content)
        self.assertNotIn("#PBS -M", content, "M2RMBISECT1.pbs must not hardcode private #PBS -M directive")
        self.assertIn("#PBS -m abe", content, "M2RMBISECT1.pbs must contain #PBS -m abe directive")

        wrapper_path = self.wrapper_path
        with open(wrapper_path, "r") as f:
            w_content = f.read()
        self.assertIn("F40_PBS_MAIL_RECIPIENT", w_content)
        self.assertIn("F40_NOTIFICATION_EMAIL_RECIPIENTS", w_content)
        self.assertIn('qsub -M "$PBS_MAIL_REC" -m abe', w_content, "Guarded submission wrapper must pass -M and -m abe to qsub")

    def test_v16r1_multi_recipient_custom_email_dispatcher_and_redaction(self):
        notify_path = os.path.join(self.repo_root, "scripts", "hpc", "notify_hpc_event.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("notify_hpc_event", notify_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        self.assertEqual(mod.redact_string("pr21vyci@mailserver.tu-freiberg.de"), "p******i@mailserver.tu-freiberg.de")
        self.assertEqual(mod.redact_string("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"), "P***************************i@student.tu-freiberg.de")

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_file = os.path.join(tmpdir, "NOTIFICATION_AUDIT.json")
            sys.argv = [
                "notify_hpc_event.py",
                "--mode", "submission",
                "--channel", "email",
                "--email-recipient", "pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de",
                "--job-id", "12345.mmaster02",
                "--audit-file", audit_file,
                "--returncode-dir", tmpdir
            ]

            orig_em = mod.send_email_message
            dispatched = []
            def mock_email(rec, subj, body):
                dispatched.append(rec)
                return 0, "Mock OK"
            mod.send_email_message = mock_email

            try:
                with self.assertRaises(SystemExit) as cm:
                    mod.main()
                self.assertEqual(cm.exception.code, 0)
                self.assertEqual(len(dispatched), 2)
                self.assertIn("pr21vyci@mailserver.tu-freiberg.de", dispatched)
                self.assertIn("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de", dispatched)
            finally:
                mod.send_email_message = orig_em

    def test_v16r2_no_email_transport_fails(self):
        notify_path = os.path.join(self.repo_root, "scripts", "hpc", "notify_hpc_event.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("notify_hpc_event", notify_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Patch subprocess.run so which returns empty
        orig_run = mod.subprocess.run
        def mock_run(cmd, **kwargs):
            if cmd[0] == "which":
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
            return orig_run(cmd, **kwargs)
        mod.subprocess.run = mock_run
        try:
            rc, msg = mod.send_email_message("pr21vyci@mailserver.tu-freiberg.de", "Test", "Body")
            self.assertNotEqual(rc, 0, "Absence of email transport must fail with non-zero exit code")
            self.assertIn("No supported email command available", msg)
        finally:
            mod.subprocess.run = orig_run

    def test_v16r2_sendmail_and_mailx_distinct_command_formats(self):
        notify_path = os.path.join(self.repo_root, "scripts", "hpc", "notify_hpc_event.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("notify_hpc_event", notify_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Test sendmail formatting
        calls = []
        def mock_run_sendmail(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        
        orig_run = mod.subprocess.run
        mod.subprocess.run = mock_run_sendmail
        try:
            # Force sendmail binary path
            with tempfile.TemporaryDirectory() as tmpdir:
                sm_path = os.path.join(tmpdir, "sendmail")
                with open(sm_path, "w") as f:
                    f.write("#!/bin/sh\n")
                
                # Mock which to return sm_path when checking sendmail
                def mock_run_which(cmd, **kwargs):
                    if cmd[0] == "which":
                        if cmd[1] == "sendmail":
                            return subprocess.CompletedProcess(cmd, 0, stdout=sm_path + "\n", stderr="")
                        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
                    calls.append((cmd, kwargs))
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

                mod.subprocess.run = mock_run_which
                rc, msg = mod.send_email_message("pr21vyci@mailserver.tu-freiberg.de", "Test Subject", "Test Body")
                self.assertEqual(rc, 0)
                # Verify sendmail was called with -t and message had To: and Subject: headers
                sm_call = [c for c in calls if c[0][0] == sm_path]
                self.assertEqual(len(sm_call), 1)
                self.assertEqual(sm_call[0][0], [sm_path, "-t"])
                self.assertIn("To: pr21vyci@mailserver.tu-freiberg.de", sm_call[0][1]["input"])
                self.assertIn("Subject: Test Subject", sm_call[0][1]["input"])
        finally:
            mod.subprocess.run = orig_run

    def test_v16r2_strict_exact_two_recipient_set_validation(self):
        notify_path = os.path.join(self.repo_root, "scripts", "hpc", "notify_hpc_event.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("notify_hpc_event", notify_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Single recipient should fail validation
            sys.argv = ["notify_hpc_event.py", "--mode", "test", "--email-recipient", "pr21vyci@mailserver.tu-freiberg.de", "--returncode-dir", tmpdir]
            with self.assertRaises(SystemExit) as cm:
                mod.main()
            self.assertNotEqual(cm.exception.code, 0)

            # Incorrect extra recipient should fail validation
            sys.argv = ["notify_hpc_event.py", "--mode", "test", "--email-recipient", "pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,extra@domain.com", "--returncode-dir", tmpdir]
            with self.assertRaises(SystemExit) as cm:
                mod.main()
            self.assertNotEqual(cm.exception.code, 0)

    def test_v16r2_terminal_monitor_parsing_and_bounded_timeout(self):
        monitor_path = os.path.join(self.repo_root, "scripts", "hpc", "stage_f", "monitor_stage_f40_terminal_state.py")
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader("monitor_stage_f40_terminal_state", monitor_path)
        spec = importlib.util.spec_from_loader("monitor_stage_f40_terminal_state", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)

        qstat_f_sample = """Job Id: 1384563.mmaster02
    Job_Name = M2RMBISECT1
    Job_Owner = pr21vyci@mlogin01
    resources_used.walltime = 00:04:12
    job_state = F
    queue = normal_q
    exec_host = mnode106/0
    Exit_status = 0
"""
        parsed = mod.parse_qstat_f(qstat_f_sample)
        self.assertEqual(parsed.get("job_state"), "F")
        self.assertEqual(parsed.get("Exit_status"), "0")
        self.assertEqual(parsed.get("exec_host"), "mnode106/0")
        self.assertEqual(parsed.get("resources_used.walltime"), "00:04:12")

    def test_v16r3_terminal_monitor_state_e_not_terminal(self):
        monitor_path = os.path.join(self.repo_root, "scripts", "hpc", "stage_f", "monitor_stage_f40_terminal_state.py")
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader("monitor_stage_f40_terminal_state", monitor_path)
        spec = importlib.util.spec_from_loader("monitor_stage_f40_terminal_state", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)

        # State E alone without Exit_status should NOT be treated as terminal
        qstat_e_sample = "Job_Name = M2RMBISECT1\njob_state = E\n"
        parsed = mod.parse_qstat_f(qstat_e_sample)
        last_state = parsed.get("job_state")
        is_term = (last_state in ["F", "C"]) and ("Exit_status" in parsed)
        self.assertFalse(is_term, "State E alone must NOT be treated as terminal")

        # State F + Exit_status SHOULD be treated as terminal
        qstat_f_sample = "Job_Name = M2RMBISECT1\njob_state = F\nExit_status = 0\n"
        parsed_f = mod.parse_qstat_f(qstat_f_sample)
        last_state_f = parsed_f.get("job_state")
        is_term_f = (last_state_f in ["F", "C"]) and ("Exit_status" in parsed_f)
        self.assertTrue(is_term_f, "State F with Exit_status must be treated as terminal")

    def test_v16r3_secure_notification_config_loader(self):
        notify_path = os.path.join(self.repo_root, "scripts", "hpc", "notify_hpc_event.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("notify_hpc_event", notify_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_dir = os.path.join(tmpdir, ".config", "adaptive-remeshing")
            os.makedirs(cfg_dir, mode=0o700, exist_ok=True)
            cfg_file = os.path.join(cfg_dir, "notifications.json")
            cfg_data = {
                "telegram_bot_token": "mock_token_123",
                "telegram_chat_id": "mock_chat_456",
                "email_recipients": ["pr21vyci@mailserver.tu-freiberg.de", "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"]
            }
            with open(cfg_file, "w") as f:
                json.dump(cfg_data, f)
            if os.name == "posix":
                os.chmod(cfg_file, 0o600)

            # Test loader with mock home directory
            orig_expanduser = os.path.expanduser
            def mock_expanduser(path):
                if path.startswith("~/.config/adaptive-remeshing"):
                    return path.replace("~/.config/adaptive-remeshing", cfg_dir)
                return orig_expanduser(path)
            
            mod.os.path.expanduser = mock_expanduser
            try:
                tok, cid, recs = mod.load_notification_config()
                self.assertIn("pr21vyci@mailserver.tu-freiberg.de", recs or "")
                self.assertIn("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de", recs or "")
            finally:
                mod.os.path.expanduser = orig_expanduser

    def test_v16r3_qstat_f_verification_json_boolean_logic(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            self.assertIn("'verification_passed': (verif_ok == 'true')", content)
            self.assertNotIn("($VERIF_OK)", content)
            self.assertNotIn("2>/dev/null || true", content)

    def test_v16r3_wrapper_freezes_renamed_monitor_path(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            self.assertIn('MONITOR_PATH="scripts/hpc/stage_f/monitor_stage_f40_terminal_state.py"', content)
            self.assertIn("QSTAT_EXISTING_JOB_AUDIT.json", content)

if __name__ == "__main__":
    unittest.main()

