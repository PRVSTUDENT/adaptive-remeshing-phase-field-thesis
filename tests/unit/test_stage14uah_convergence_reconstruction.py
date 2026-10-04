import os
import json
import unittest

class TestStage14UAHConvergenceReconstruction(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.pkg28_dir = os.path.join(self.repo_root, 'models', 'pandey_kumar_mode1', '28_stage14_convergence_control_candidate')
        self.report_json = os.path.join(self.pkg28_dir, 'MODE1_STAGE14UAH_CONVERGENCE_RECONSTRUCTION_REPORT.json')
        self.fortran_src = os.path.join(self.pkg28_dir, 'f42_mixed_uel.for')
        self.inp_deck = os.path.join(self.pkg28_dir, 'PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL.inp')

    def test_report_json_and_attempt_reconstruction(self):
        self.assertTrue(os.path.exists(self.report_json), f"Missing report JSON: {self.report_json}")
        with open(self.report_json, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data['stage'], 'Stage 14U-AH')
        self.assertEqual(data['governing_gate'], 'GATE_6B_ACTIVE_EVALUATION_AND_CONTINUATION')
        
        attempts = data['increment_2890_attempts']
        self.assertEqual(len(attempts), 10, "Increment 2890 must have exactly 10 reconstructed cutback attempts")
        
        # Check initial and terminal attempts
        self.assertAlmostEqual(attempts[0]['dt'], 2.0e-4, places=8)
        self.assertAlmostEqual(attempts[9]['dt'], 1.0e-9, places=12)

    def test_residual_pass_margin_gt_1000x(self):
        with open(self.report_json, 'r') as f:
            data = json.load(f)
            
        attempts = data['increment_2890_attempts']
        for att in attempts:
            margin = att['R_margin_factor']
            self.assertGreater(margin, 1000.0, f"Attempt {att['attempt']} residual margin {margin} must exceed 1000x")
            self.assertAlmostEqual(att['R_max_kN'], 1.942e-9, places=12)
            self.assertAlmostEqual(att['R_tol_kN'], 2.090e-6, places=9)

    def test_solution_correction_divergence(self):
        with open(self.report_json, 'r') as f:
            data = json.load(f)
            
        attempts = data['increment_2890_attempts']
        for att in attempts:
            self.assertEqual(att['controlling_node'], 13628)
            self.assertEqual(att['controlling_dof'], 3)
            self.assertEqual(att['outcome'], 'REJECTED_SOLUTION_CORRECTION_ONLY')
            
        ratios = [att['c_ratio'] for att in attempts]
        self.assertTrue(all(x < y for x, y in zip(ratios, ratios[1:])), "Rejection ratios must increase monotonically with dt cutbacks")
        self.assertAlmostEqual(ratios[0], 22.22, places=1)
        self.assertGreater(ratios[-1], 1.0e6)

    def test_epistemic_classifications(self):
        with open(self.report_json, 'r') as f:
            data = json.load(f)
            
        ep = data['executive_summary']['epistemic_classifications']
        self.assertEqual(ep['H1_residual_margin_gt_1000x'], 'SOURCE_AND_NUMERICALLY_VERIFIED')
        self.assertEqual(ep['H2_correction_criterion_only'], 'SOURCE_AND_NUMERICALLY_VERIFIED')
        self.assertEqual(ep['H3_history_nonsmoothness_wake_node'], 'SOURCE_AND_NUMERICALLY_VERIFIED')
        self.assertEqual(ep['H4_post_fracture_normalization_sensitivity'], 'POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED')
        self.assertEqual(ep['H4b_matrix_ill_conditioning'], 'NOT_ESTABLISHED')

    def test_fortran_boundlessness_and_gradient_distinction(self):
        self.assertTrue(os.path.exists(self.fortran_src), f"Missing Fortran source: {self.fortran_src}")
        with open(self.fortran_src, 'r') as f:
            content = f.read()
            
        # Verify no explicit projection / clipping on damage variable
        self.assertNotIn('min(max(d', content.lower())
        self.assertNotIn('max(0.0d0, min(1.0d0', content.lower())
        self.assertNotIn('if (d .gt. 1.0', content.lower())
        self.assertNotIn('if (d > 1.0', content.lower())
        
        # Verify weak form contains spatial gradient regularization term
        self.assertTrue('e_gc*e_l0' in content.lower().replace(' ', '') or '(e_gc*e_l0)*bdb' in content.lower().replace(' ', ''))

    def test_package28_controls_syntax_and_derivation(self):
        self.assertTrue(os.path.exists(self.inp_deck), f"Missing input deck: {self.inp_deck}")
        with open(self.inp_deck, 'r') as f:
            lines = f.readlines()
            
        controls_found = False
        params_found = False
        for i, line in enumerate(lines):
            if '*CONTROLS, PARAMETERS=FIELD, FIELD=DISPLACEMENT' in line:
                controls_found = True
                if i + 1 < len(lines) and '0.005, 0.50' in lines[i+1]:
                    params_found = True
                    break
                    
        self.assertTrue(controls_found, "Missing *CONTROLS, PARAMETERS=FIELD, FIELD=DISPLACEMENT in Step 2")
        self.assertTrue(params_found, "Missing 0.005, 0.50 parameter line under *CONTROLS")

if __name__ == '__main__':
    unittest.main()
