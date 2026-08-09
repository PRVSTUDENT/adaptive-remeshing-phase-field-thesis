#!/usr/bin/env python3
"""Offline unit tests for Stage F32 M2RMBUILD7 static qualification gate."""

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class TestF32M2RMBUILD7StaticGate(unittest.TestCase):

    def test_write_input_exactAssignment_absent(self):
        builder = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/runtime/build_f32_geometry_backed_model.py"
        self.assertTrue(builder.exists(), "F32 builder script missing")
        content = builder.read_text(encoding="utf-8")
        self.assertNotIn("exactAssignment", content, "writeInput exactAssignment argument must be absent")

    def test_write_input_consistencyChecking_on_present(self):
        builder = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/runtime/build_f32_geometry_backed_model.py"
        content = builder.read_text(encoding="utf-8")
        self.assertIn("job.writeInput(consistencyChecking=ON)", content, "job.writeInput(consistencyChecking=ON) signature must be present")
        self.assertIn("from abaqusConstants import", content, "Explicit ON import required")
        self.assertIn("ON", content)

    def test_cae_environment_variable_argument_transport(self):
        builder = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/runtime/build_f32_geometry_backed_model.py"
        pbs = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/M2RMBUILD7.pbs"
        
        b_content = builder.read_text(encoding="utf-8")
        p_content = pbs.read_text(encoding="utf-8")

        self.assertIn("F32_SOURCE_DECK", b_content)
        self.assertIn("F32_OUTPUT_INPUT", b_content)
        self.assertIn("F32_GEOMETRY_AUDIT", b_content)

        self.assertIn("export F32_SOURCE_DECK=", p_content)
        self.assertIn("export F32_OUTPUT_INPUT=", p_content)
        self.assertIn("export F32_GEOMETRY_AUDIT=", p_content)
        self.assertNotIn("abaqus cae noGUI=runtime/build_f32_geometry_backed_model.py --", p_content, "No '-- arguments' transport allowed")

    def test_pbs_work_dir_self_staging(self):
        pbs = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/M2RMBUILD7.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn('cp "$F32_PACKAGE_DIR/M2RMBUILD7.pbs" .', content, "M2RMBUILD7.pbs must stage itself into WORK_DIR before SHA verification")

    def test_pbs_sha256sum_manifest_checks(self):
        pbs = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/M2RMBUILD7.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("sha256sum -c SHA256SUMS", content, "sha256sum -c SHA256SUMS must be executed in PBS")
        self.assertIn("sha256sum -c F32_SHA256SUMS", content, "sha256sum -c F32_SHA256SUMS must be executed in PBS")

    def test_terminal_notification_trap_on_all_paths(self):
        pbs = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/M2RMBUILD7.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("trap on_exit EXIT", content, "EXIT trap must be installed")
        self.assertIn("term_curl_rc=$?", content, "Explicit curl exit code capture required")
        self.assertNotIn("curl ... || echo", content, "Command substitution echo fallback prohibited")

    def test_runtime_status_classifications(self):
        pbs = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/M2RMBUILD7.pbs"
        content = pbs.read_text(encoding="utf-8")
        self.assertIn("cae_geometry_build_contract_passed", content)
        self.assertIn("cae_geometry_build_contract_failed", content)
        self.assertNotIn("f32_m2rmbuild7_static_clean_linux_qualified_not_authorized", content, "Authorization classification must not be in runtime STATUS.json")

    def test_prohibited_solver_and_remesh_calls(self):
        builder = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/runtime/build_f32_geometry_backed_model.py"
        pbs = ROOT / "models/generated/mode_ii/f32_cae_runtime_gate_repair/M2RMBUILD7.pbs"
        
        b_content = builder.read_text(encoding="utf-8")
        p_content = pbs.read_text(encoding="utf-8")

        self.assertNotIn("abaqus job=", b_content.lower())
        self.assertNotIn("abaqus standard", p_content.lower())
        self.assertNotIn("adaptiveremesh", b_content.lower())

if __name__ == "__main__":
    unittest.main()
