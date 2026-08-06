import os
import sys
import json
import unittest
import tempfile
import shutil
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_f38_comprehensive_cae_diagnostic_gate import validate_f38_static_gate

class TestStageF38Batch(unittest.TestCase):

    def test_f38_static_gate(self):
        self.assertTrue(validate_f38_static_gate())

    def test_entrypoint_has_no_file_token(self):
        entry_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/run_f38_cae_diagnostic.py"
        content = entry_path.read_text(encoding="utf-8")
        self.assertNotIn("__file__", content)

    def test_entrypoint_execution_without_file_global(self):
        runtime_dir = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime"
        os.environ["F38_RUNTIME_DIR"] = str(runtime_dir)

        tmp_dir = tempfile.mkdtemp()
        try:
            audit_file = os.path.join(tmp_dir, "CAE_INVOCATION_CONTEXT_AUDIT.json")
            os.environ["F38_INVOCATION_AUDIT"] = audit_file

            entry_path = runtime_dir / "run_f38_cae_diagnostic.py"
            code = compile(entry_path.read_text(encoding="utf-8"), str(entry_path), "exec")

            globs = {
                "__name__": "__main__",
                "__builtins__": __builtins__
            }
            self.assertNotIn("__file__", globs)

            class MockMatrix:
                @staticmethod
                def main():
                    pass

            sys.modules["f38_cae_diagnostic_matrix"] = MockMatrix

            exec(code, globs)

            self.assertTrue(os.path.exists(audit_file))
            with open(audit_file, "r") as f:
                audit_data = json.load(f)
            self.assertFalse(audit_data["file_global_defined"])
            self.assertTrue(audit_data["bootstrap_passed"])
        finally:
            shutil.rmtree(tmp_dir)

    def test_mandatory_runtime_dir(self):
        entry_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/run_f38_cae_diagnostic.py"
        code = compile(entry_path.read_text(encoding="utf-8"), str(entry_path), "exec")

        old_val = os.environ.pop("F38_RUNTIME_DIR", None)
        try:
            globs = {"__name__": "__main__", "__builtins__": __builtins__}
            with self.assertRaises(RuntimeError) as cm:
                exec(code, globs)
            self.assertIn("F38_RUNTIME_DIR", str(cm.exception))
        finally:
            if old_val is not None:
                os.environ["F38_RUNTIME_DIR"] = old_val

    def test_status_before_missing_evidence_report_in_pbs(self):
        pbs_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/M2RMDIAG1.pbs"
        content = pbs_path.read_text(encoding="utf-8")
        status_idx = content.find("STATUS.json")
        report_idx = content.find("generate_missing_evidence_report.py")
        self.assertNotEqual(status_idx, -1)
        self.assertNotEqual(report_idx, -1)
        self.assertLess(status_idx, report_idx, "STATUS.json must be written before generate_missing_evidence_report.py is called")

    def test_persistent_evidence_copying_in_pbs(self):
        pbs_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/M2RMDIAG1.pbs"
        content = pbs_path.read_text(encoding="utf-8")
        self.assertIn("F38_EVIDENCE_DIR", content)
        self.assertIn('cp "$f" "$F38_EVIDENCE_DIR/"', content)
        self.assertIn("STATUS.json", content)
        self.assertIn("CAE_PHASE_DIAGNOSTIC_MATRIX.json", content)

    def test_runtime_validator_invocation_in_pbs(self):
        pbs_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/M2RMDIAG1.pbs"
        content = pbs_path.read_text(encoding="utf-8")
        self.assertIn("validate_f38_runtime_audits.py", content)
        self.assertIn("runtime_val_rc", content)

    def test_no_cross_model_part_usage(self):
        matrix_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/f38_cae_diagnostic_matrix.py"
        content = matrix_path.read_text(encoding="utf-8")
        inst_idx = content.find("def phase_instance_replacement")
        self.assertNotEqual(inst_idx, -1)
        next_idx = content.find("def phase_crack_edge_method_inventory")
        inst_func = content[inst_idx:next_idx]
        self.assertIn("Part2DGeomFrom2DMesh", inst_func)
        self.assertNotIn("geom_part = ctx.get('geom_part')", inst_func, "phase_instance_replacement must construct its own geometry part inside its own model")

    def test_no_hardcoded_topology_pass(self):
        matrix_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/f38_cae_diagnostic_matrix.py"
        content = matrix_path.read_text(encoding="utf-8")
        topo_idx = content.find("def phase_crack_mesh_topology")
        self.assertNotEqual(topo_idx, -1)
        next_idx = content.find("def phase_assembly_set_inventory")
        topo_func = content[topo_idx:next_idx]
        self.assertIn("intersection_count", topo_func)
        self.assertIn("coincident_node_pairs_count", topo_func)
        self.assertIn("bridge_element_count", topo_func)

    def test_dependency_blocked_behavior(self):
        sys.path.insert(0, str(ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime"))
        import f38_cae_diagnostic_matrix as mat

        matrix = {"phases": []}
        passed_phases = {"model_import": False}
        res = mat.run_phase(matrix, "repository_inventory", lambda ctx: {}, {}, passed_phases)
        self.assertFalse(res)
        self.assertEqual(len(matrix["phases"]), 1)
        rec = matrix["phases"][0]
        self.assertFalse(rec["attempted"])
        self.assertTrue(rec["dependency_blocked"])
        self.assertIn("model_import", rec["blocked_by"])

    def test_separate_model_features_instances_inventory(self):
        matrix_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/f38_cae_diagnostic_matrix.py"
        content = matrix_path.read_text(encoding="utf-8")
        self.assertIn("assembly.features", content)
        self.assertIn("assembly.instances", content)
        self.assertIn("feature_instance_diff", content)

    def test_individual_output_variable_probing(self):
        matrix_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/f38_cae_diagnostic_matrix.py"
        content = matrix_path.read_text(encoding="utf-8")
        out_idx = content.find("def phase_output_variable_probe")
        self.assertNotEqual(out_idx, -1)
        next_idx = content.find("def phase_output_request_rebinding")
        out_func = content[out_idx:next_idx]
        self.assertIn("model.fieldOutputRequests", out_func)
        self.assertIn("accepted_variables", out_func)
        self.assertIn("rejected_variables", out_func)

    def test_zero_solver_datacheck_remesh_or_nested_submissions(self):
        pkg_dir = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix"
        for p in pkg_dir.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".pbs", ".sh"):
                text = p.read_text(encoding="utf-8").lower()
                self.assertNotIn("abaqus job=", text, f"Prohibited solver invocation in {p}")
                self.assertNotIn("abaqus standard", text, f"Prohibited standard solver in {p}")
                self.assertNotIn("adaptiveremesh", text, f"Prohibited adaptiveRemesh in {p}")

    def test_exactly_one_guarded_qsub_path(self):
        orch_path = ROOT / "scripts/hpc/stage_f/submit_stage_f38_cae_diagnostic.sh"
        content = orch_path.read_text(encoding="utf-8")
        self.assertIn("F38_ALLOW_SUBMISSION", content)
        self.assertIn("F38_AUTHORIZE_M2RMDIAG1", content)
        qsub_matches = re.findall(r"(?m)^JOB_ID=\$\(qsub\s", content)
        self.assertEqual(len(qsub_matches), 1)

    def test_f37_package_unmodified(self):
        f37_dir = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair"
        manifest_path = f37_dir / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        import hashlib
        files_map = manifest.get("package_files") or manifest.get("files") or {}
        for rel_path, expected_hash in files_map.items():
            file_path = f37_dir / rel_path
            self.assertTrue(file_path.exists(), f"F37 file {rel_path} missing")
            h = hashlib.sha256(file_path.read_bytes()).hexdigest()
            self.assertEqual(h, expected_hash, f"F37 file {rel_path} modified!")

if __name__ == "__main__":
    unittest.main()
