import json
from pathlib import Path
import unittest


class TestPackage148R5TerminalEvaluation(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.eval_path = self.root / 'results/validation/package148_r5_terminal_evaluation.json'
        self.runtime_path = self.root / 'results/validation/package148_r5_terminal_runtime.json'

    def test_evaluation_exists_and_schema_valid(self):
        self.assertTrue(self.eval_path.exists(), f"Missing: {self.eval_path}")
        data = json.loads(self.eval_path.read_text(encoding='utf-8'))
        self.assertEqual(data.get('schema'), 1)
        self.assertEqual(data.get('pbs_job_id'), '1418909.mmaster02')
        self.assertEqual(data.get('job_name'), 'M1_C4_P148_R5')

    def test_outer_iteration_count_and_convergence(self):
        data = json.loads(self.eval_path.read_text(encoding='utf-8'))
        self.assertEqual(data['outer_iterations_completed'], 15)
        metrics = data['convergence_metrics']
        self.assertLess(metrics['delta_d_outer_15'], 2.5e-5)
        self.assertLess(metrics['delta_u_outer_15_mm'], 1.0e-8)
        self.assertEqual(metrics['dual_error_outer_15'], 0.0)

    def test_physical_acceptance_tolerances_pass(self):
        data = json.loads(self.eval_path.read_text(encoding='utf-8'))
        comp = data['donor_comparison_package_146']
        self.assertLess(comp['rf2_deficit_pct'], 5.0)
        self.assertLess(comp['energy_deficit_pct'], 2.0)
        self.assertEqual(comp['rf2_gate'], 'PASS')
        self.assertEqual(comp['energy_gate'], 'PASS')
        self.assertEqual(comp['damage_bounds_gate'], 'PASS')
        self.assertEqual(comp['damage_irreversibility_gate'], 'PASS')

    def test_root_cause_identified(self):
        data = json.loads(self.eval_path.read_text(encoding='utf-8'))
        self.assertIn('timeout=780', data['root_cause'])
        self.assertIn('outer 15', data['root_cause'])


if __name__ == '__main__':
    unittest.main()
