import unittest
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F24_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f24_geometry_and_odb_compatibility_gate')
PACKAGE_DIR = os.path.join(ROOT, 'models', 'generated', 'mode_ii', 'f24_geometry_and_odb_compatibility_gate')

class TestF24GeometryAndODBGate(unittest.TestCase):

    def test_official_adaptive_remesh_contract_rules(self):
        path = os.path.join(F24_DIR, 'OFFICIAL_ADAPTIVE_REMESH_CONTRACT.json')
        self.assertTrue(os.path.isfile(path), 'missing OFFICIAL_ADAPTIVE_REMESH_CONTRACT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(len(data.get('official_contract_rules', [])), 11)

    def test_geometry_backed_model_contract_order(self):
        path = os.path.join(F24_DIR, 'GEOMETRY_BACKED_MODEL_CONTRACT.json')
        self.assertTrue(os.path.isfile(path), 'missing GEOMETRY_BACKED_MODEL_CONTRACT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(len(data.get('model_construction_order', [])), 17)
        self.assertEqual(data.get('geometry_backed_part_name'), 'Part-1-GEOM')
        self.assertEqual(data.get('geometry_backed_instance_name'), 'Part-1-1')

    def test_source_odb_compatibility_audit(self):
        path = os.path.join(F24_DIR, 'SOURCE_ODB_COMPATIBILITY_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing SOURCE_ODB_COMPATIBILITY_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('target_odb'), 'M2MISER1.odb')
        self.assertFalse(data.get('region_correspondence_valid'))
        self.assertEqual(data.get('compatibility_decision'), 'provisional_analysis_required')

    def test_f24_decision_outcome_b(self):
        path = os.path.join(F24_DIR, 'F24_DECISION.json')
        self.assertTrue(os.path.isfile(path), 'missing F24_DECISION.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('selected_outcome'), 'Outcome B')
        self.assertEqual(data.get('decision_classification'), 'matching_geometry_backed_provisional_analysis_required')
        self.assertEqual(data.get('final_classification'), 'f24_m2rmprov1_clean_linux_qualified_not_authorized')
        self.assertEqual(data.get('prepared_job'), 'M2RMPROV1')
        self.assertFalse(data.get('m2rmexec2_prepared'))
        self.assertFalse(data.get('execution_authorized'))

    def test_precall_recognition_audit_spec(self):
        path = os.path.join(F24_DIR, 'PRECALL_RECOGNITION_AUDIT_SPEC.json')
        self.assertTrue(os.path.isfile(path), 'missing PRECALL_RECOGNITION_AUDIT_SPEC.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(len(data.get('audit_fields', [])), 21)
        self.assertEqual(data.get('pass_criteria', {}).get('selected_remesh_route'), 'Model.adaptiveRemesh(odb)')

    def test_evidence_retention_contract(self):
        path = os.path.join(F24_DIR, 'EVIDENCE_RETENTION_CONTRACT.json')
        self.assertTrue(os.path.isfile(path), 'missing EVIDENCE_RETENTION_CONTRACT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(len(data.get('required_evidence_files', [])), 10)

    def test_no_execution_audit(self):
        path = os.path.join(F24_DIR, 'NO_EXECUTION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing NO_EXECUTION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertFalse(data.get('execution_authorized'))
        self.assertEqual(data.get('qsub_attempts'), 0)
        self.assertEqual(data.get('successful_submissions'), 0)
        self.assertEqual(data.get('solver_executions'), 0)
        self.assertEqual(data.get('model_adaptiveRemesh_calls'), 0)

    def test_m2rmprov1_package_files_exist(self):
        for name in ('M2RMPROV1.inp', 'M2RMPROV1.pbs', 'F24_CLEAN_LINUX_QUALIFICATION.json', 'F24_NO_EXECUTION_AUDIT.json'):
            path = os.path.join(PACKAGE_DIR, name)
            self.assertTrue(os.path.isfile(path), 'missing package file ' + name)

    def test_submit_orchestrator_exists_and_guarded(self):
        import re
        path = os.path.join(ROOT, 'scripts', 'hpc', 'stage_f', 'submit_stage_f24_provisional_analysis.sh')
        self.assertTrue(os.path.isfile(path), 'missing submit_stage_f24_provisional_analysis.sh')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('F24_ACTIVATE_SUBMISSION', content)
        self.assertIn('F24_EXPLICIT_AUTHORIZATION', content)
        qsub_calls = re.findall(r'\bqsub\b', content)
        self.assertEqual(len(qsub_calls), 1)

    def test_validator_script_passes(self):
        import scripts.validation.validate_f24_geometry_and_odb_gate as val
        rc = val.main()
        self.assertEqual(rc, 0, 'Validator script failed')

    def test_bootstrap_validation(self):
        import scripts.validation.check_multi_agent_bootstrap as boot
        rc = boot.main([])
        self.assertEqual(rc, 0, 'Bootstrap check failed with return code %d' % rc)

if __name__ == '__main__':
    unittest.main()
