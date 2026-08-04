# Python 2 and 3 compatible unit tests for Stage F30
from __future__ import print_function
import unittest
import os
import json
import subprocess
import sys

class TestStageF30CAERuntimeGateRepair(unittest.TestCase):

    def setUp(self):
        self.runs_dir = 'runs/hpc/stage_f/f30_cae_runtime_gate_repair'
        self.pkg_dir = 'models/generated/mode_ii/f30_cae_runtime_gate_repair'
        self.orch_script = 'scripts/hpc/stage_f/submit_stage_f30_cae_build_qualification.sh'

    def test_01_f29_invalidation_audit(self):
        inv_path = os.path.join(self.runs_dir, 'F29_INVALIDATION_AUDIT.json')
        self.assertTrue(os.path.exists(inv_path))
        with open(inv_path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data.get('corrected_classification'), 'f29_m2rmbuild4_package_invalid_no_submission_authorized')
        self.assertFalse(data.get('submission_authorized'))
        self.assertGreaterEqual(len(data.get('blocking_defects', [])), 10)

    def test_02_abaqus_topology_api_audit(self):
        audit_path = os.path.join(self.runs_dir, 'ABAQUS_TOPOLOGY_API_AUDIT.json')
        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, 'r') as f:
            data = json.load(f)
        self.assertTrue(data.get('edge_get_faces_returns_integer_ids'))
        self.assertTrue(data.get('direct_pointOn_on_edge_getFaces_prohibited'))

    def test_03_mesh_connectivity_audit_contract(self):
        conn_path = os.path.join(self.runs_dir, 'MESH_CONNECTIVITY_AUDIT_CONTRACT.json')
        self.assertTrue(os.path.exists(conn_path))
        with open(conn_path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data.get('required_bridge_element_count'), 0)
        self.assertTrue(data.get('direct_connectivity_vs_label_comparison_prohibited'))

    def test_04_source_output_contract_separate_requests(self):
        out_path = os.path.join(self.runs_dir, 'SOURCE_OUTPUT_CONTRACT.json')
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, 'r') as f:
            data = json.load(f)
        self.assertIn('node_output', data)
        self.assertIn('element_output', data)
        self.assertEqual(data['node_output']['region_type'], 'model')
        self.assertEqual(data['element_output']['region_name'], 'All_elem')

    def test_05_builder_script_api_fixes(self):
        builder_path = os.path.join(self.pkg_dir, 'runtime', 'build_f30_geometry_backed_model.py')
        self.assertTrue(os.path.exists(builder_path))
        with open(builder_path, 'r') as f:
            content = f.read()
        self.assertIn("face_ids = e.getFaces()", content)
        self.assertIn("geom_part.faces[i]", content)
        self.assertIn("elem.getNodes()", content)
        self.assertIn("F-Output-1", content)
        self.assertIn("F-Output-2", content)
        self.assertIn("expected_source_entity_keys", content)

    def test_06_pbs_script_ordering_and_staging(self):
        pbs_path = os.path.join(self.pkg_dir, 'M2RMBUILD5.pbs')
        self.assertTrue(os.path.exists(pbs_path))
        with open(pbs_path, 'r') as f:
            content = f.read()
        self.assertIn("set -Eeuo pipefail", content)
        self.assertIn("cp \"$F30_PACKAGE_DIR/SOURCE_ENTITY_SPEC.json\" .", content)
        # Check runtime validation order: validate_generated_input before validate_f30_runtime_audits
        idx_gen = content.find("validate_generated_input.py")
        idx_run = content.find("validate_f30_runtime_audits.py")
        self.assertNotEqual(idx_gen, -1)
        self.assertNotEqual(idx_run, -1)
        self.assertLess(idx_gen, idx_run)

    def test_07_generated_input_validator(self):
        val_path = os.path.join(self.pkg_dir, 'runtime', 'validate_generated_input.py')
        self.assertTrue(os.path.exists(val_path))
        with open(val_path, 'r') as f:
            content = f.read()
        self.assertIn("has_instance_part11", content)
        self.assertIn("has_equation_kw", content)
        self.assertIn("has_bc_bottom_values", content)
        self.assertIn("has_miseseri_group", content)

    def test_08_runtime_validator_imports_os(self):
        val_path = os.path.join(self.pkg_dir, 'runtime', 'validate_f30_runtime_audits.py')
        self.assertTrue(os.path.exists(val_path))
        with open(val_path, 'r') as f:
            content = f.read()
        self.assertIn("import os", content)

    def test_09_orchestrator_repository_relative_path(self):
        self.assertTrue(os.path.exists(self.orch_script))
        with open(self.orch_script, 'r') as f:
            content = f.read()
        self.assertIn("PACKAGE_REL_PATH=\"models/generated/mode_ii/f30_cae_runtime_gate_repair\"", content)
        self.assertIn("git ls-tree -r \"$PREP_SHA\" \"$PACKAGE_REL_PATH\"", content)

    def test_10_offline_validator_passes(self):
        val_script = 'scripts/validation/validate_f30_cae_runtime_gate_repair.py'
        self.assertTrue(os.path.exists(val_script))
        python_exe = sys.executable
        res = subprocess.run([python_exe, val_script], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn('"classification": "pass"', res.stdout)

if __name__ == '__main__':
    unittest.main()
