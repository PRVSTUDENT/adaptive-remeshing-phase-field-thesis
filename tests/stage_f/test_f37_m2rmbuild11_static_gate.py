#!/usr/bin/env python3
"""Offline unit tests for Stage F37 M2RMBUILD11 static qualification gate."""

import json
import os
import sys
import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPAT_PATH = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/f37_runtime_compat.py"
SPEC = importlib.util.spec_from_file_location("f37_runtime_compat", str(COMPAT_PATH))
compat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compat)

class TestF37M2RMBUILD11StaticGate(unittest.TestCase):

    def test_exact_upper_and_mixed_case_resolution(self):
        for key in ('Part-1', 'PART-1', 'pArT-1'):
            result = compat.resolve_unique_repository_key({key: object()}, 'Part-1', 'test')
            self.assertEqual(result['resolved_key'], key)

    def test_zero_ambiguous_and_non_string_failures(self):
        with self.assertRaises(RuntimeError):
            compat.resolve_unique_repository_key({'Other': object()}, 'Part-1', 'test')
        with self.assertRaises(RuntimeError):
            compat.resolve_unique_repository_key({'Part-1': object(), 'PART-1': object()}, 'Part-1', 'test')
        with self.assertRaises(TypeError):
            compat.resolve_unique_repository_key({1: object()}, 'Part-1', 'test')

    def test_embedded_runtime_hardening_and_order(self):
        pkg = ROOT / 'models/generated/mode_ii/f37_cae_python_compatibility_repair'
        builder = (pkg / 'runtime/build_f37_geometry_backed_model.py').read_text(encoding='utf-8')
        pbs = (pkg / 'M2RMBUILD11.pbs').read_text(encoding='utf-8')
        self.assertNotIn('.casefold(', builder)
        self.assertNotIn("m.parts['Part-1']", builder)
        self.assertNotIn("a.instances['Part-1-1']", builder)
        self.assertIn('from f37_runtime_compat import resolve_unique_repository_key', builder)
        self.assertLess(pbs.index('abaqus python'), pbs.index('abaqus cae'))
        self.assertLess(pbs.index('cat << EOF > STATUS.json'), pbs.index('generate_missing_evidence_report.py'))
        self.assertIn('RUNTIME_FAILURE_AUDIT.json', pbs)

    def test_probe_and_builder_use_same_compatibility_module(self):
        pkg = ROOT / 'models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime'
        for name in ('build_f37_geometry_backed_model.py', 'probe_f37_python_compatibility.py'):
            self.assertIn('from f37_runtime_compat import resolve_unique_repository_key', (pkg / name).read_text(encoding='utf-8'))

    def test_abaqus_scripts_reject_modern_only_constructs(self):
        runtime = ROOT / 'models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime'
        for name in ('build_f37_geometry_backed_model.py', 'f37_runtime_compat.py', 'probe_f37_python_compatibility.py'):
            content = (runtime / name).read_text(encoding='utf-8')
            for token in ('.casefold(', 'pathlib', 'dataclasses', 'subprocess.run', 'exist_ok='):
                self.assertNotIn(token, content)

    def test_wrapper_one_qsub_and_no_retry_loop(self):
        content = (ROOT / 'scripts/hpc/stage_f/submit_stage_f37_cae_build_qualification.sh').read_text(encoding='utf-8')
        commands = [line for line in content.splitlines() if line.strip().startswith('JOB_ID=$(qsub ')]
        self.assertEqual(len(commands), 1)
        self.assertNotRegex(content, r'(?m)^\s*(for|while|until)\b.*qsub')

    def test_write_input_exactAssignment_absent(self):
        builder = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
        self.assertTrue(builder.exists(), "F37 builder script missing")
        content = builder.read_text(encoding="utf-8")
        self.assertNotIn("exactAssignment", content, "writeInput exactAssignment argument must be absent")

    def test_write_input_consistencyChecking_on_present(self):
        builder = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        self.assertIn("job.writeInput(consistencyChecking=ON)", content, "job.writeInput(consistencyChecking=ON) signature must be present")
        self.assertIn("from abaqusConstants import", content, "Explicit ON import required")
        self.assertIn("ON", content)

    def test_abaqus_2023_constant_import_is_minimal_and_validated(self):
        builder = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        self.assertNotIn("UNPLANNED", content)
        self.assertIn("from abaqusConstants import ON, CPE4, STANDARD, STRUCTURED", content)

    def test_full_model_import_and_slit_endpoint_api(self):
        builder = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        self.assertIn("mdb.ModelFromInputFile", content)
        self.assertNotIn("PartFromInputFile", content)
        self.assertIn("edge.getVertices()", content)
        self.assertNotIn("p1, p2 = edge.pointOn[0]", content)
        self.assertIn("crack_x_min = -0.5", content)
        self.assertIn("crack_x_max = 0.0", content)

    def test_all_required_runtime_audits_are_written_from_live_objects(self):
        builder = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        for name in ("SOURCE_MODEL_INVENTORY.json", "INSTANCE_REPLACEMENT_API_AUDIT.json", "MODEL_ENTITY_REBINDING_AUDIT.json", "SLIT_GEOMETRY_AUDIT.json", "SLIT_MESH_TOPOLOGY_AUDIT.json", "GEOMETRY_BACKED_MODEL_AUDIT.json", "GENERATED_INPUT_AUDIT.json"):
            self.assertIn(name, content)
        self.assertIn("source_contract_coverage", content)

    def test_cae_environment_variable_argument_transport(self):
        builder = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
        pbs = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"

        b_content = builder.read_text(encoding="utf-8")
        p_content = pbs.read_text(encoding="utf-8")

        self.assertIn("F37_SOURCE_DECK", b_content)
        self.assertIn("F37_OUTPUT_INPUT", b_content)
        self.assertIn("F37_GEOMETRY_AUDIT", b_content)

        self.assertIn("export F37_SOURCE_DECK=", p_content)
        self.assertIn("export F37_OUTPUT_INPUT=", p_content)
        self.assertIn("export F37_GEOMETRY_AUDIT=", p_content)
        self.assertNotIn("abaqus cae noGUI=runtime/build_f37_geometry_backed_model.py --", p_content, "No '-- arguments' transport allowed")

    def test_pbs_work_dir_self_staging(self):
        pbs = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn('cp "$F37_PACKAGE_DIR/M2RMBUILD11.pbs" .', content, "M2RMBUILD11.pbs must stage itself into WORK_DIR before SHA verification")

    def test_pbs_sha256sum_manifest_checks(self):
        pbs = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("sha256sum -c SHA256SUMS", content, "sha256sum -c SHA256SUMS must be executed in PBS")
        self.assertIn("sha256sum -c F37_SHA256SUMS", content, "sha256sum -c F37_SHA256SUMS must be executed in PBS")

    def test_terminal_notification_trap_on_all_paths(self):
        pbs = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("trap on_exit EXIT", content, "EXIT trap must be installed")
        self.assertIn("term_curl_rc=$?", content, "Explicit curl exit code capture required")
        self.assertNotIn("curl ... || echo", content, "Command substitution echo fallback prohibited")

    def test_verified_python3_and_actual_returncode_capture(self):
        pbs = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertNotRegex(content, r"(?m)^\s*python\s+")
        self.assertIn("command -v python3", content)
        self.assertIn('cae_builder_rc="skipped"', content)
        self.assertIn("set +e\nabaqus cae", content)
        self.assertIn("cae_builder_rc=$?\nset -e", content)
        self.assertIn("python3 \"$WORK_DIR/runtime/validate_generated_input.py\"", content)

    def test_runtime_status_classifications(self):
        pbs = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("cae_geometry_build_contract_passed", content)
        self.assertIn("cae_geometry_build_contract_failed", content)
        self.assertNotIn("f37_m2rmbuild11_static_clean_linux_qualified_not_authorized", content, "Authorization classification must not be in runtime STATUS.json")

    def test_prohibited_solver_and_remesh_calls(self):
        builder = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
        pbs = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"

        b_content = builder.read_text(encoding="utf-8")
        p_content = pbs.read_text(encoding="utf-8")

        self.assertNotIn("abaqus job=", b_content.lower())
        self.assertNotIn("abaqus standard", p_content.lower())
        self.assertNotIn("adaptiveremesh", b_content.lower())

if __name__ == "__main__":
    unittest.main()
