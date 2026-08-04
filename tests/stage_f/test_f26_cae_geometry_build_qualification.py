import unittest
import json
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F26_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f26_cae_geometry_build_qualification')
PACKAGE_DIR = os.path.join(ROOT, 'models', 'generated', 'mode_ii', 'f26_cae_geometry_build_qualification')

class TestF26CAEGeometryBuildQualification(unittest.TestCase):

    def test_f25_invalidation_audit(self):
        path = os.path.join(F26_DIR, 'F25_INVALIDATION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing F25_INVALIDATION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('f25_qualification_invalidated'))
        self.assertEqual(data.get('corrected_f25_classification'), 'f25_m2rmprov1_package_invalid_no_submission_authorized')

    def test_cae_builder_script_fail_closed(self):
        path = os.path.join(PACKAGE_DIR, 'runtime', 'build_f26_geometry_backed_model.py')
        self.assertTrue(os.path.isfile(path), 'missing build_f26_geometry_backed_model.py')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('from abaqus import mdb', content)
        self.assertIn('Part2DGeomFrom2DMesh', content)
        self.assertIn('SectionAssignment', content)
        self.assertIn('ElemType', content)
        self.assertIn('setElementType', content)
        self.assertIn('setMeshControls', content)
        self.assertIn('seedPart', content)
        self.assertIn('generateMesh', content)
        self.assertIn('Instance', content)
        self.assertIn('regenerate', content)
        self.assertIn('Region', content)
        self.assertIn('RemeshingRule', content)
        self.assertIn('job.writeInput', content)
        # Ensure no broad exception catching that converts failure to fallback
        self.assertNotIn('real_build_used = False', content)

    def test_pbs_execution_contract_and_wrapper(self):
        pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD1.pbs')
        self.assertTrue(os.path.isfile(pbs_path), 'missing M2RMBUILD1.pbs')
        with open(pbs_path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('module load abaqus/2023', content)
        self.assertNotIn('|| python3', content)
        self.assertNotIn('abaqus job=', content)
        self.assertIn('NOTIFICATION_START_TELEGRAM.json', content)
        self.assertIn('NOTIFICATION_TERMINAL_TELEGRAM.json', content)
        self.assertIn('build_f26_geometry_backed_model.py', content)
        self.assertIn('send_telegram', content)

    def test_execution_counters(self):
        path = os.path.join(F26_DIR, 'EXECUTION_COUNTERS.json')
        self.assertTrue(os.path.isfile(path), 'missing EXECUTION_COUNTERS.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('cae_builder_calls'), 1)
        self.assertEqual(data.get('standard_solver_calls'), 0)
        self.assertEqual(data.get('adaptive_remesh_calls'), 0)
        self.assertEqual(data.get('datacheck_calls'), 0)

    def test_f26_decision_gate(self):
        path = os.path.join(F26_DIR, 'F26_DECISION.json')
        self.assertTrue(os.path.isfile(path), 'missing F26_DECISION.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('final_classification'), 'f26_m2rmbuild1_clean_linux_qualified_not_authorized')
        self.assertFalse(data.get('execution_authorized'))

    def test_no_execution_audit(self):
        path = os.path.join(F26_DIR, 'NO_EXECUTION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing NO_EXECUTION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertFalse(data.get('execution_authorized'))
        self.assertEqual(data.get('qsub_attempts'), 0)

    def test_submit_orchestrator_exists_and_guarded(self):
        path = os.path.join(ROOT, 'scripts', 'hpc', 'stage_f', 'submit_stage_f26_cae_build_qualification.sh')
        self.assertTrue(os.path.isfile(path), 'missing submit_stage_f26_cae_build_qualification.sh')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('F26_ACTIVATE_SUBMISSION', content)
        self.assertIn('F26_EXPLICIT_AUTHORIZATION', content)
        qsub_calls = re.findall(r'\bqsub\b', content)
        self.assertEqual(len(qsub_calls), 1)

    def test_validator_script_passes(self):
        import scripts.validation.validate_f26_cae_geometry_build_qualification as val
        rc = val.main()
        self.assertEqual(rc, 0, 'Validator script failed')

    def test_bootstrap_validation(self):
        import scripts.validation.check_multi_agent_bootstrap as boot
        rc = boot.main([])
        self.assertEqual(rc, 0, 'Bootstrap check failed with return code %d' % rc)

if __name__ == '__main__':
    unittest.main()
