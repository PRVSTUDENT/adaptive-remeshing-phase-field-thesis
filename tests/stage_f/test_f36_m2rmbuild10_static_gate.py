#!/usr/bin/env python3
"""Offline unit tests for Stage F36 M2RMBUILD10 static qualification gate."""

from __future__ import annotations
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class TestF36M2RMBUILD10StaticGate(unittest.TestCase):

    def test_write_input_exactAssignment_absent(self):
        builder = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/runtime/build_f36_geometry_backed_model.py"
        self.assertTrue(builder.exists(), "F36 builder script missing")
        content = builder.read_text(encoding="utf-8")
        self.assertNotIn("exactAssignment", content, "writeInput exactAssignment argument must be absent")

    def test_write_input_consistencyChecking_on_present(self):
        builder = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/runtime/build_f36_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        self.assertIn("job.writeInput(consistencyChecking=ON)", content, "job.writeInput(consistencyChecking=ON) signature must be present")
        self.assertIn("from abaqusConstants import", content, "Explicit ON import required")
        self.assertIn("ON", content)

    def test_abaqus_2023_constant_import_is_minimal_and_validated(self):
        builder = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/runtime/build_f36_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        self.assertNotIn("UNPLANNED", content)
        self.assertIn("from abaqusConstants import ON, CPE4, STANDARD, STRUCTURED", content)

    def test_full_model_import_and_slit_endpoint_api(self):
        builder = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/runtime/build_f36_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        self.assertIn("mdb.ModelFromInputFile", content)
        self.assertNotIn("PartFromInputFile", content)
        self.assertIn("edge.getVertices()", content)
        self.assertNotIn("p1, p2 = edge.pointOn[0]", content)
        self.assertIn("crack_x_min = -0.5", content)
        self.assertIn("crack_x_max = 0.0", content)

    def test_all_required_runtime_audits_are_written_from_live_objects(self):
        builder = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/runtime/build_f36_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        for name in ("SOURCE_MODEL_INVENTORY.json", "INSTANCE_REPLACEMENT_API_AUDIT.json", "MODEL_ENTITY_REBINDING_AUDIT.json", "SLIT_GEOMETRY_AUDIT.json", "SLIT_MESH_TOPOLOGY_AUDIT.json", "GEOMETRY_BACKED_MODEL_AUDIT.json", "GENERATED_INPUT_AUDIT.json"):
            self.assertIn(name, content)
        self.assertIn("source_contract_coverage", content)

    def test_cae_environment_variable_argument_transport(self):
        builder = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/runtime/build_f36_geometry_backed_model.py"
        pbs = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/M2RMBUILD10.pbs"

        b_content = builder.read_text(encoding="utf-8")
        p_content = pbs.read_text(encoding="utf-8")

        self.assertIn("F36_SOURCE_DECK", b_content)
        self.assertIn("F36_OUTPUT_INPUT", b_content)
        self.assertIn("F36_GEOMETRY_AUDIT", b_content)

        self.assertIn("export F36_SOURCE_DECK=", p_content)
        self.assertIn("export F36_OUTPUT_INPUT=", p_content)
        self.assertIn("export F36_GEOMETRY_AUDIT=", p_content)
        self.assertNotIn("abaqus cae noGUI=runtime/build_f36_geometry_backed_model.py --", p_content, "No '-- arguments' transport allowed")

    def test_pbs_work_dir_self_staging(self):
        pbs = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/M2RMBUILD10.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn('cp "$F36_PACKAGE_DIR/M2RMBUILD10.pbs" .', content, "M2RMBUILD10.pbs must stage itself into WORK_DIR before SHA verification")

    def test_pbs_sha256sum_manifest_checks(self):
        pbs = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/M2RMBUILD10.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("sha256sum -c SHA256SUMS", content, "sha256sum -c SHA256SUMS must be executed in PBS")
        self.assertIn("sha256sum -c F36_SHA256SUMS", content, "sha256sum -c F36_SHA256SUMS must be executed in PBS")

    def test_terminal_notification_trap_on_all_paths(self):
        pbs = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/M2RMBUILD10.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("trap on_exit EXIT", content, "EXIT trap must be installed")
        self.assertIn("term_curl_rc=$?", content, "Explicit curl exit code capture required")
        self.assertNotIn("curl ... || echo", content, "Command substitution echo fallback prohibited")

    def test_verified_python3_and_actual_returncode_capture(self):
        pbs = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/M2RMBUILD10.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertNotIn("python ", content)
        self.assertIn("command -v python3", content)
        self.assertIn('cae_builder_rc="skipped"', content)
        self.assertIn("set +e\nabaqus cae", content)
        self.assertIn("cae_builder_rc=$?\nset -e", content)
        self.assertIn("python3 \"$WORK_DIR/runtime/validate_generated_input.py\"", content)

    def test_runtime_status_classifications(self):
        pbs = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/M2RMBUILD10.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("cae_geometry_build_contract_passed", content)
        self.assertIn("cae_geometry_build_contract_failed", content)
        self.assertNotIn("f36_m2rmbuild10_static_clean_linux_qualified_not_authorized", content, "Authorization classification must not be in runtime STATUS.json")

    def test_prohibited_solver_and_remesh_calls(self):
        builder = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/runtime/build_f36_geometry_backed_model.py"
        pbs = ROOT / "models/generated/mode_ii/f36_cae_import_key_repair/M2RMBUILD10.pbs"

        b_content = builder.read_text(encoding="utf-8")
        p_content = pbs.read_text(encoding="utf-8")

        self.assertNotIn("abaqus job=", b_content.lower())
        self.assertNotIn("abaqus standard", p_content.lower())
        self.assertNotIn("adaptiveremesh", b_content.lower())

if __name__ == "__main__":
    unittest.main()
