"""Regression for R6's pre-solve failure and the distinct R7 startup contract."""
import unittest
from pathlib import Path
from scripts.validation.validate_package148_r7_startup import validate
from scripts.validation.execute_package148_state_transfer import operation_contract

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'models/pandey_kumar_mode1'


class StartupContract(unittest.TestCase):
    def test_r6_reproduces_exact_startup_rejection(self):
        with self.assertRaisesRegex(ValueError, 'Unreviewed legacy GP ordering'):
            validate(BASE/'148_c4_package148_state_transfer_r6')

    def test_r7_actual_loader_and_all_history_cards(self):
        result = validate(BASE/'148_c4_package148_state_transfer_r7')
        self.assertEqual(result['history_mappings'], 28224)
        self.assertFalse(result['solver_executed'])

    def test_registered_revision_has_distinct_once_only_job(self):
        manifest, job, qualification = operation_contract('evaluate_mode1_package148_state_transfer_r7')
        self.assertIn('_r7/', manifest)
        self.assertEqual(job, 'M1_C4_P148_R7')
        self.assertTrue(qualification.endswith('_r7.qualification.json'))


if __name__ == '__main__':
    unittest.main()
