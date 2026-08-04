import unittest
import json
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F27_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f27_cae_build_package_repair')
PACKAGE_DIR = os.path.join(ROOT, 'models', 'generated', 'mode_ii', 'f27_cae_build_package_repair')

class TestF27CAEBuildPackageRepair(unittest.TestCase):

    def test_f26_invalidation_audit(self):
        path = os.path.join(F27_DIR, 'F26_INVALIDATION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing F26_INVALIDATION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('f26_qualification_invalidated'))
        self.assertEqual(data.get('corrected_f26_classification'), 'f26_m2rmbuild1_package_invalid_no_submission_authorized')

    def test_abaqus_api_corrections(self):
        path = os.path.join(PACKAGE_DIR, 'runtime', 'build_f27_geometry_backed_model.py')
        self.assertTrue(os.path.isfile(path), 'missing build_f27_geometry_backed_model.py')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('STANDARD', content)
        self.assertIn("variables=('MISESERI',)", content)
        self.assertNotIn('errorIndicator=', content)
        self.assertNotIn('orphan_instance.suppress()', content)
        self.assertIn('assembly.suppressFeatures', content)
        self.assertIn('assembly.renameFeature', content)
        self.assertIn('MODEL_ENTITY_REBINDING_AUDIT.json', content)

    def test_instance_replacement_audit(self):
        path = os.path.join(F27_DIR, 'INSTANCE_REPLACEMENT_API_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing INSTANCE_REPLACEMENT_API_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('api_audit_pass'))
        self.assertEqual(data.get('final_active_geometry_instance'), 'Part-1-1')

    def test_model_entity_rebinding_contract(self):
        path = os.path.join(F27_DIR, 'MODEL_ENTITY_REBINDING_CONTRACT.json')
        self.assertTrue(os.path.isfile(path), 'missing MODEL_ENTITY_REBINDING_CONTRACT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('required_unresolved_count'), 0)
        self.assertTrue(data.get('contract_pass_required'))

    def test_pbs_execution_contract_and_wrapper(self):
        pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD2.pbs')
        self.assertTrue(os.path.isfile(pbs_path), 'missing M2RMBUILD2.pbs')
        with open(pbs_path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('/scratch/pr21vyci/', content)
        self.assertIn('module load gcc/11.4.0', content)
        self.assertIn('module load abaqus/2023', content)
        self.assertIn('notifications.env', content)
        self.assertIn('ok', content)
        self.assertIn('NOTIFICATION_START_TELEGRAM.json', content)
        self.assertIn('NOTIFICATION_TERMINAL_TELEGRAM.json', content)
        self.assertIn('build_f27_geometry_backed_model.py', content)
        self.assertNotIn('|| true', content)

    def test_execution_counters(self):
        path = os.path.join(F27_DIR, 'EXECUTION_COUNTERS.json')
        self.assertTrue(os.path.isfile(path), 'missing EXECUTION_COUNTERS.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('cae_builder_calls'), 1)
        self.assertEqual(data.get('standard_solver_calls'), 0)
        self.assertEqual(data.get('compatibility_checks'), 1)

    def test_f27_decision_gate(self):
        path = os.path.join(F27_DIR, 'F27_DECISION.json')
        self.assertTrue(os.path.isfile(path), 'missing F27_DECISION.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('final_classification'), 'f27_m2rmbuild2_clean_linux_qualified_not_authorized')
        self.assertFalse(data.get('execution_authorized'))

    def test_no_execution_audit(self):
        path = os.path.join(F27_DIR, 'NO_EXECUTION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing NO_EXECUTION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertFalse(data.get('execution_authorized'))
        self.assertEqual(data.get('qsub_attempts'), 0)

    def test_submit_orchestrator_exists_and_guarded(self):
        path = os.path.join(ROOT, 'scripts', 'hpc', 'stage_f', 'submit_stage_f27_cae_build_qualification.sh')
        self.assertTrue(os.path.isfile(path), 'missing submit_stage_f27_cae_build_qualification.sh')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('32c3f1f6df35e3fa7a8bb7605b2fe893ce4932a0', content)
        self.assertIn('F27_ACTIVATE_SUBMISSION', content)
        self.assertIn('F27_EXPLICIT_AUTHORIZATION', content)
        qsub_calls = re.findall(r'\bqsub\b', content)
        self.assertEqual(len(qsub_calls), 1)

    def test_validator_script_passes(self):
        import scripts.validation.validate_f27_cae_build_package_repair as val
        rc = val.main()
        self.assertEqual(rc, 0, 'Validator script failed')

    def test_bootstrap_validation(self):
        import scripts.validation.check_multi_agent_bootstrap as boot
        rc = boot.main([])
        self.assertEqual(rc, 0, 'Bootstrap check failed with return code %d' % rc)

if __name__ == '__main__':
    unittest.main()
