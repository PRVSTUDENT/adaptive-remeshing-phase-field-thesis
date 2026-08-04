import unittest
import json
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F29_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f29_topology_safe_cae_build')
PACKAGE_DIR = os.path.join(ROOT, 'models', 'generated', 'mode_ii', 'f29_topology_safe_cae_build')

class TestF29TopologySafeCAEBuild(unittest.TestCase):

    def test_f28_invalidation_audit(self):
        path = os.path.join(F29_DIR, 'F28_INVALIDATION_AUDIT.json')
        self.assertTrue(os.path.isfile(path), 'missing F28_INVALIDATION_AUDIT.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertTrue(data.get('f28_qualification_invalidated'))
        self.assertEqual(data.get('corrected_f28_classification'), 'f28_m2rmbuild3_package_invalid_no_submission_authorized')

    def test_source_contracts_and_topology_contracts(self):
        for item in ['SOURCE_ENTITY_SPEC.json', 'SOURCE_REGION_MAP.json', 'SOURCE_OUTPUT_CONTRACT.json', 'SOURCE_SLIT_TOPOLOGY_CONTRACT.json']:
            path = os.path.join(F29_DIR, item)
            self.assertTrue(os.path.isfile(path), 'missing ' + item)
            with open(path, 'r', encoding='utf-8') as h:
                d = json.load(h)
            self.assertEqual(d.get('task_id'), 'F29-INVALIDATE-F28-AND-PREPARE-TOPOLOGY-SAFE-CAE-BUILD')

    def test_abaqus_builder_topology_and_rebinding_apis(self):
        path = os.path.join(PACKAGE_DIR, 'runtime', 'build_f29_geometry_backed_model.py')
        self.assertTrue(os.path.isfile(path), 'missing build_f29_geometry_backed_model.py')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('STANDARD', content)
        self.assertIn("variables=('MISESERI',)", content)
        self.assertNotIn('assembly.renameFeature', content)
        self.assertNotIn('orphan_instance.suppress()', content)
        self.assertIn('assembly.deleteFeatures', content)
        self.assertIn('pointOn[0][1]', content)
        self.assertIn("assembly.Set(name='All_elem', elements=inst_ref.elements)", content)
        self.assertIn('FieldOutputRequest', content)

    def test_runtime_validation_scripts_imports(self):
        for script in ['validate_f29_runtime_audits.py', 'generate_missing_evidence_report.py', 'validate_generated_input.py']:
            path = os.path.join(PACKAGE_DIR, 'runtime', script)
            self.assertTrue(os.path.isfile(path), 'missing ' + script)
            with open(path, 'r', encoding='utf-8') as h:
                text = h.read()
            self.assertIn('import os', text)

    def test_pbs_execution_contract_and_wrapper(self):
        pbs_path = os.path.join(PACKAGE_DIR, 'M2RMBUILD4.pbs')
        self.assertTrue(os.path.isfile(pbs_path), 'missing M2RMBUILD4.pbs')
        with open(pbs_path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('/scratch/pr21vyci/', content)
        self.assertIn('notifications.env', content)
        self.assertIn('exit 15', content)
        self.assertIn('exit 17', content)
        self.assertIn('trap - EXIT', content)
        self.assertNotIn('abaqus job=', content)

    def test_execution_counters(self):
        path = os.path.join(F29_DIR, 'EXECUTION_COUNTERS.json')
        self.assertTrue(os.path.isfile(path), 'missing EXECUTION_COUNTERS.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('cae_builder_calls'), 0)
        self.assertEqual(data.get('standard_solver_calls'), 0)

    def test_f29_decision_gate(self):
        path = os.path.join(F29_DIR, 'F29_DECISION.json')
        self.assertTrue(os.path.isfile(path), 'missing F29_DECISION.json')
        with open(path, 'r', encoding='utf-8') as h:
            data = json.load(h)
        self.assertEqual(data.get('final_classification'), 'f29_m2rmbuild4_static_clean_linux_qualified_not_authorized')
        self.assertFalse(data.get('execution_authorized'))

    def test_submit_orchestrator_exists_and_guarded(self):
        path = os.path.join(ROOT, 'scripts', 'hpc', 'stage_f', 'submit_stage_f29_cae_build_qualification.sh')
        self.assertTrue(os.path.isfile(path), 'missing submit_stage_f29_cae_build_qualification.sh')
        with open(path, 'r', encoding='utf-8') as h:
            content = h.read()
        self.assertIn('PACKAGE_PREP_SHA="b2a3535742a08961688ee5e65dbe4c8e412e4118"', content)
        self.assertIn('git merge-base --is-ancestor', content)
        self.assertIn('git diff --quiet', content)
        self.assertIn('git ls-tree -r', content)
        qsub_calls = re.findall(r'\bqsub\b', content)
        self.assertEqual(len(qsub_calls), 1)

    def test_validator_script_passes(self):
        import scripts.validation.validate_f29_topology_safe_cae_build as val
        rc = val.main()
        self.assertEqual(rc, 0, 'Validator script failed')

    def test_bootstrap_validation(self):
        import scripts.validation.check_multi_agent_bootstrap as boot
        rc = boot.main([])
        self.assertEqual(rc, 0, 'Bootstrap check failed with return code %d' % rc)

if __name__ == '__main__':
    unittest.main()
