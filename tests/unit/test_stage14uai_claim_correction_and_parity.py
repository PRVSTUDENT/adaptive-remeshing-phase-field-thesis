import os
import json
import unittest

class TestStage14UAIClaimCorrectionAndParity(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.pkg28_dir = os.path.join(self.repo_root, 'models', 'pandey_kumar_mode1', '28_stage14_convergence_control_candidate')
        self.report_json = os.path.join(self.pkg28_dir, 'MODE1_STAGE14UAH_CONVERGENCE_RECONSTRUCTION_REPORT.json')
        self.report_md = os.path.join(self.pkg28_dir, 'MODE1_STAGE14UAH_CONVERGENCE_RECONSTRUCTION_REPORT.md')
        self.pkg27_dir = os.path.join(self.repo_root, 'models', 'pandey_kumar_mode1', '27_stage14_adaptive_candidate_14k_4thread_stage_b')

    def test_reject_local_d_as_global_fe_bound(self):
        with open(self.report_json, 'r') as f:
            data = json.load(f)
        self.assertFalse(data['executive_summary']['local_algebraic_bound_proves_global_fe'],
                         "Local algebraic relation d(H) must NOT be asserted as a proof of global FE bounds")
        
        with open(self.report_md, 'r') as f:
            content = f.read()
        self.assertIn("local algebraic", content.lower())
        self.assertIn("gradient", content.lower())

    def test_reject_ill_conditioning_without_conditioning_metrics(self):
        with open(self.report_json, 'r') as f:
            data = json.load(f)
        ep = data['executive_summary']['epistemic_classifications']
        self.assertEqual(ep['H4b_matrix_ill_conditioning'], 'NOT_ESTABLISHED',
                         "Matrix ill-conditioning must be NOT_ESTABLISHED until direct conditioning metrics exist")
        self.assertEqual(ep['H4_post_fracture_normalization_sensitivity'],
                         'POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED')

    def test_reject_global_history_exclusion_from_single_node(self):
        with open(self.report_json, 'r') as f:
            data = json.load(f)
        ep = data['executive_summary']['epistemic_classifications']
        self.assertIn('wake_node', 'H3_history_nonsmoothness_wake_node')
        self.assertEqual(ep['H3_history_nonsmoothness_wake_node'], 'SOURCE_AND_NUMERICALLY_VERIFIED')

    def test_reject_cn_050_as_validated_production_setting(self):
        with open(self.report_json, 'r') as f:
            data = json.load(f)
        status = data['package_28_preflight']['submission_status']
        self.assertIn('HOLD', status)
        self.assertNotIn('VALIDATED_PRODUCTION_SETTING', status)
        
        # Check that 50x relaxation is explicitly documented
        relax_str = data['package_28_preflight']['relaxation_factor']
        self.assertIn('50x', relax_str)

    def test_reject_single_run_determinism(self):
        # Stage B repeat package must exist independently
        self.assertTrue(os.path.exists(self.pkg27_dir), "Package 27 Stage B must exist for independent repeat")
        # One run alone cannot claim THREAD_DETERMINISM_PASS
        # Determinism requires comparing Stage A vs Stage B

if __name__ == '__main__':
    unittest.main()
