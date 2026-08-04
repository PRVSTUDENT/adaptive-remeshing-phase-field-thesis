import json
import os
import subprocess
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
F23_DIR = os.path.join(ROOT, 'runs', 'hpc', 'stage_f', 'f23_offline_adaptive_region_investigation')

class TestF23AdaptiveRegionInvestigation(unittest.TestCase):

    def text(self, rel):
        with open(os.path.join(ROOT, rel), encoding='utf-8') as h:
            return h.read()

    def json_data(self, rel):
        return json.loads(self.text(rel))

    def test_f20_f21_contract_comparison(self):
        comp = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/F20_F21_CONTRACT_COMPARISON.json')
        self.assertEqual(comp['f20_job'], 'M2RMREG7')
        self.assertEqual(comp['f21_job'], 'M2RMEXEC1')
        self.assertFalse(comp['f20_adaptiveRemesh_executed'])
        self.assertTrue(comp['f21_adaptiveRemesh_executed'])
        self.assertIn('AbaqusException', comp['f21_failure_exception'])
        self.assertIn('root_cause_explanation', comp)

    def test_zero_recognized_adaptive_region_detection(self):
        spec = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/PRECALL_RECOGNITION_AUDIT_SPEC.json')
        self.assertEqual(spec['fail_closed_threshold'], 'recognized_adaptive_region_count > 0')
        self.assertFalse(spec['fallback_allowed'])
        self.assertIn('recognized_adaptive_region_count', spec['audit_fields_required'])

    def test_positive_recognized_adaptive_region_fixture_spec(self):
        spec = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/PRECALL_RECOGNITION_AUDIT_SPEC.json')
        self.assertEqual(spec['zero_count_action'], 'fail closed immediately before invoking model.adaptiveRemesh')

    def test_exact_selected_api_route_and_no_fallback(self):
        evidence = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/ADAPTIVE_REGION_API_EVIDENCE.json')
        self.assertGreater(evidence['unresolved_count'], 0)
        self.assertEqual(evidence['hypotheses_evaluated']['hypothesis_4']['evidence_status'], 'rejected_by_evidence')

    def test_rule_existence_not_treated_as_region_recognition(self):
        comp = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/F20_F21_CONTRACT_COMPARISON.json')
        self.assertEqual(comp['f20_qualification_basis'], 'rule_creation_and_non_null_region_check_only')

    def test_geometry_backed_part_instance_association_evaluated(self):
        evidence = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/ADAPTIVE_REGION_API_EVIDENCE.json')
        h1 = evidence['hypotheses_evaluated']['hypothesis_1']
        self.assertEqual(h1['evidence_status'], 'plausible_unproven_offline')

    def test_precall_failure_behavior_and_retention(self):
        audit = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/EVIDENCE_RETENTION_REPAIR_AUDIT.json')
        self.assertIn('SOURCE_MESH_SUMMARY.json', audit['required_retained_files'])
        self.assertIn('cae.returncode', audit['required_retained_files'])
        self.assertIn('collector.returncode', audit['required_retained_files'])
        self.assertIn('first_failure.returncode', audit['required_retained_files'])
        self.assertIn('MISSING_EVIDENCE_REPORT.json', audit['required_retained_files'])

    def test_collector_return_code_retention_and_cae_preservation(self):
        audit = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/EVIDENCE_RETENTION_REPAIR_AUDIT.json')
        self.assertIn('masking_prevention_rule', audit)
        self.assertIn('exit_code_priority', audit)

    def test_zero_execution_counters(self):
        no_exec = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/NO_EXECUTION_AUDIT.json')
        for k in ('solver_executions', 'datacheck_executions', 'adaptivity_process_submissions',
                  'model_adaptiveRemesh_calls', 'native_remesh_calls', 'candidates_generated',
                  'refined_analyses', 'qsub_attempts'):
            self.assertEqual(no_exec[k], 0)

    def test_decision_gate_outcome_b(self):
        decision = self.json_data('runs/hpc/stage_f/f23_offline_adaptive_region_investigation/ADAPTIVE_REGION_ASSOCIATION_DECISION.json')
        self.assertEqual(decision['selected_outcome'], 'Outcome B')
        self.assertEqual(decision['decision_classification'], 'adaptive_region_association_unresolved_offline')
        self.assertEqual(decision['final_classification'], 'f23_adaptive_region_association_unresolved_no_job_prepared')
        self.assertFalse(decision['m2rmexec2_prepared'])
        self.assertFalse(decision['execution_authorized'])
        self.assertFalse(decision['submission_approved'])
        self.assertEqual(decision['qsub_attempts'], 0)

    def test_python_2_compatibility(self):
        compat = self.text('models/generated/mode_ii/f21_native_remesh_execution/runtime/f21_abaqus_python_compatibility.py')
        self.assertIn('sys.version_info', compat)

    def test_json_parsing_all_f23_artifacts(self):
        for name in ('F20_F21_CONTRACT_COMPARISON.json', 'ADAPTIVE_REGION_API_EVIDENCE.json',
                     'ADAPTIVE_REGION_ASSOCIATION_DECISION.json', 'PRECALL_RECOGNITION_AUDIT_SPEC.json',
                     'EVIDENCE_RETENTION_REPAIR_AUDIT.json', 'NO_EXECUTION_AUDIT.json'):
            path = os.path.join(F23_DIR, name)
            self.assertTrue(os.path.isfile(path), 'missing ' + name)
            with open(path, 'r', encoding='utf-8') as h:
                data = json.load(h)
            self.assertIsInstance(data, dict)

    def test_validator_script_passes(self):
        import scripts.validation.validate_f23_adaptive_region_investigation as val
        errs = val.validate()
        self.assertEqual(errs, [], 'Validator returned errors: %s' % errs)

    def test_bootstrap_validation(self):
        import scripts.validation.check_multi_agent_bootstrap as boot
        rc = boot.main([])
        self.assertEqual(rc, 0, 'Bootstrap check failed with return code %d' % rc)

if __name__ == '__main__':
    unittest.main()
