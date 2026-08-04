import unittest
import json
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F25_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f25_geometry_backed_provisional_package_repair')
PACKAGE_DIR = os.path.join(ROOT, 'models', 'generated', 'mode_ii', 'f25_geometry_backed_provisional_package_repair')

class TestF25GeometryBackedProvisionalPackageRepair(unittest.TestCase):

    def test_f24_invalidation_audit(self):
        path = os.path.join(F25_DIR, 'F24_INVALIDATION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing F24_INVALIDATION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('f24_qualification_invalid'))
        self.assertIn('build_f24_geometry_backed_model.py performs only a raw file copy of source_deck.inp', data.get('invalidation_evidence', []))

    def test_real_geometry_builder_audit(self):
        path = os.path.join(F25_DIR, 'REAL_GEOMETRY_BUILDER_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing REAL_GEOMETRY_BUILDER_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('uses_real_abaqus_apis'))
        self.assertIn('abaqus.mdb', data.get('required_abaqus_modules', []))

    def test_geometry_backed_model_audit_contract_pass(self):
        path = os.path.join(PACKAGE_DIR, 'GEOMETRY_BACKED_MODEL_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing GEOMETRY_BACKED_MODEL_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('contract_pass'))
        self.assertTrue(data.get('generated_differs_from_source'))
        self.assertGreater(data.get('geometry_face_count', 0), 0)

    def test_generated_input_deck_exists_and_differs(self):
        gen_inp = os.path.join(PACKAGE_DIR, 'M2RMPROV1.inp')
        src_inp = os.path.join(PACKAGE_DIR, 'runtime', 'source_deck.inp')
        self.assertTrue(os.path.isfile(gen_inp), 'missing M2RMPROV1.inp')
        self.assertTrue(os.path.isfile(src_inp), 'missing source_deck.inp')
        self.assertGreater(os.path.getsize(gen_inp), 0)
        with open(gen_inp, 'rb') as f1, open(src_inp, 'rb') as f2:
            self.assertNotEqual(f1.read(), f2.read(), 'M2RMPROV1.inp must not be identical to source_deck.inp')

    def test_pbs_execution_contract_and_wrapper(self):
        pbs_path = os.path.join(PACKAGE_DIR, 'M2RMPROV1.pbs')
        self.assertTrue(os.path.isfile(pbs_path), 'missing M2RMPROV1.pbs')
        with open(pbs_path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('module load abaqus', content)
        self.assertIn('NOTIFICATION_START_TELEGRAM.json', content)
        self.assertIn('NOTIFICATION_TERMINAL_TELEGRAM.json', content)
        self.assertIn('build_f25_geometry_backed_model.py', content)
        self.assertIn('GEOMETRY_BACKED_MODEL_AUDIT.json', content)
        self.assertIn('F25_PACKAGE_DIR', content)
        self.assertIn('F25_EVIDENCE_DIR', content)

    def test_f25_decision_gate(self):
        path = os.path.join(F25_DIR, 'F25_DECISION.json')
        self.assertTrue(os.path.isfile(path), 'missing F25_DECISION.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('final_classification'), 'f25_m2rmprov1_real_geometry_builder_clean_linux_qualified_not_authorized')
        self.assertFalse(data.get('execution_authorized'))

    def test_no_execution_audit(self):
        path = os.path.join(F25_DIR, 'NO_EXECUTION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing NO_EXECUTION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertFalse(data.get('execution_authorized'))
        self.assertEqual(data.get('qsub_attempts'), 0)

    def test_submit_orchestrator_exists_and_guarded(self):
        path = os.path.join(ROOT, 'scripts', 'hpc', 'stage_f', 'submit_stage_f25_provisional_analysis.sh')
        self.assertTrue(os.path.isfile(path), 'missing submit_stage_f25_provisional_analysis.sh')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('F25_ACTIVATE_SUBMISSION', content)
        self.assertIn('F25_EXPLICIT_AUTHORIZATION', content)
        qsub_calls = re.findall(r'\bqsub\b', content)
        self.assertEqual(len(qsub_calls), 1)

    def test_validator_script_passes(self):
        import scripts.validation.validate_f25_geometry_backed_provisional_package_repair as val
        rc = val.main()
        self.assertEqual(rc, 0, 'Validator script failed')

    def test_bootstrap_validation(self):
        import scripts.validation.check_multi_agent_bootstrap as boot
        rc = boot.main([])
        self.assertEqual(rc, 0, 'Bootstrap check failed with return code %d' % rc)

if __name__ == '__main__':
    unittest.main()
