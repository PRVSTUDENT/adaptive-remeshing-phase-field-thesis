import unittest
import json
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F28_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f28_real_cae_build_package')
PACKAGE_DIR = os.path.join(ROOT, 'models', 'generated', 'mode_ii', 'f28_real_cae_build_package')

class TestF28RealCAEBuildPackage(unittest.TestCase):

    def test_f27_invalidation_audit(self):
        path = os.path.join(F28_DIR, 'F27_INVALIDATION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing F27_INVALIDATION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('f27_qualification_invalidated'))
        self.assertEqual(data.get('corrected_f27_classification'), 'f27_m2rmbuild2_package_invalid_no_submission_authorized')

    def test_source_entity_spec_and_region_map(self):
        spec_path = os.path.join(F28_DIR, 'SOURCE_ENTITY_SPEC.json')
        map_path = os.path.join(F28_DIR, 'SOURCE_REGION_MAP.json')
        self.assertTrue(os.path.isfile(spec_path), 'missing SOURCE_ENTITY_SPEC.json')
        self.assertTrue(os.path.isfile(map_path), 'missing SOURCE_REGION_MAP.json')
        with open(spec_path, 'r', encoding='utf-8') as h:
            spec = json.load(h)
        with open(map_path, 'r', encoding='utf-8') as h:
            rmap = json.load(h)
        self.assertEqual(spec.get('task_id'), 'F28-INVALIDATE-F27-AND-COMPLETE-REAL-CAE-BUILD-PACKAGE')
        self.assertTrue(len(rmap.get('regions', [])) >= 6)

    def test_abaqus_builder_reconstruction_apis(self):
        path = os.path.join(PACKAGE_DIR, 'runtime', 'build_f28_geometry_backed_model.py')
        self.assertTrue(os.path.isfile(path), 'missing build_f28_geometry_backed_model.py')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('STANDARD', content)
        self.assertIn("variables=('MISESERI',)", content)
        self.assertNotIn('assembly.renameFeature', content)
        self.assertNotIn('orphan_instance.suppress()', content)
        self.assertIn('assembly.deleteFeatures', content)
        self.assertIn('m.constraints', content)
        self.assertIn('geom_part.Set', content)
        self.assertIn('assembly.Set', content)
        self.assertIn('m.DisplacementBC', content)
        self.assertIn('m.Equation', content)

    def test_instance_replacement_audit(self):
        path = os.path.join(F28_DIR, 'INSTANCE_REPLACEMENT_API_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing INSTANCE_REPLACEMENT_API_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('api_audit_pass'))
        self.assertEqual(data.get('final_active_geometry_instance'), 'Part-1-1')

    def test_model_entity_rebinding_contract(self):
        path = os.path.join(F28_DIR, 'MODEL_ENTITY_REBINDING_CONTRACT.json')
        self.assertTrue(os.path.isfile(path), 'missing MODEL_ENTITY_REBINDING_CONTRACT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('required_unresolved_count'), 0)
        self.assertEqual(data.get('required_stale_orphan_reference_count'), 0)

    def test_pbs_execution_contract_and_wrapper(self):
        pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD3.pbs')
        self.assertTrue(os.path.isfile(pbs_path), 'missing M2RMBUILD3.pbs')
        with open(pbs_path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('/scratch/pr21vyci/', content)
        self.assertIn('module load gcc/11.4.0', content)
        self.assertIn('module load abaqus/2023', content)
        self.assertIn('notifications.env', content)
        self.assertIn('trap - EXIT', content)
        self.assertIn('build_f28_geometry_backed_model.py', content)
        self.assertNotIn('abaqus job=', content)

    def test_execution_counters(self):
        path = os.path.join(F28_DIR, 'EXECUTION_COUNTERS.json')
        self.assertTrue(os.path.isfile(path), 'missing EXECUTION_COUNTERS.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('cae_builder_calls'), 1)
        self.assertEqual(data.get('standard_solver_calls'), 0)

    def test_f28_decision_gate(self):
        path = os.path.join(F28_DIR, 'F28_DECISION.json')
        self.assertTrue(os.path.isfile(path), 'missing F28_DECISION.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('final_classification'), 'f28_m2rmbuild3_static_clean_linux_qualified_not_authorized')
        self.assertFalse(data.get('execution_authorized'))

    def test_no_execution_audit(self):
        path = os.path.join(F28_DIR, 'NO_EXECUTION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing NO_EXECUTION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertFalse(data.get('execution_authorized'))
        self.assertEqual(data.get('qsub_attempts'), 0)

    def test_submit_orchestrator_exists_and_guarded(self):
        path = os.path.join(ROOT, 'scripts', 'hpc', 'stage_f', 'submit_stage_f28_cae_build_qualification.sh')
        self.assertTrue(os.path.isfile(path), 'missing submit_stage_f28_cae_build_qualification.sh')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('PACKAGE_PREP_SHA="7c2c680bad77301a2d2f8f13c4f001b80eb5827d"', content)
        self.assertIn('git merge-base --is-ancestor', content)
        self.assertIn('F28_ACTIVATE_SUBMISSION', content)
        self.assertIn('F28_EXPLICIT_AUTHORIZATION', content)
        qsub_calls = re.findall(r'\bqsub\b', content)
        self.assertEqual(len(qsub_calls), 1)

    def test_validator_script_passes(self):
        import scripts.validation.validate_f28_real_cae_build_package as val
        rc = val.main()
        self.assertEqual(rc, 0, 'Validator script failed')

    def test_bootstrap_validation(self):
        import scripts.validation.check_multi_agent_bootstrap as boot
        rc = boot.main([])
        self.assertEqual(rc, 0, 'Bootstrap check failed with return code %d' % rc)

if __name__ == '__main__':
    unittest.main()
