"""Regression for the distinct R8 startup contract."""
import unittest
from pathlib import Path
from scripts.validation.validate_package148_r8_startup import validate
from scripts.validation.execute_package148_state_transfer import operation_contract

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'models/pandey_kumar_mode1'


class R8StartupContract(unittest.TestCase):
    def test_r8_actual_loader_and_all_history_cards(self):
        result = validate(BASE/'148_c4_package148_state_transfer_r8')
        self.assertEqual(result['history_mappings'], 28224)
        self.assertEqual(result['max_outer'], 40)
        self.assertFalse(result['solver_executed'])

    def test_registered_revision_has_distinct_once_only_job(self):
        manifest, job, qualification = operation_contract('evaluate_mode1_package148_state_transfer_r8')
        self.assertIn('_r8/', manifest)
        self.assertEqual(job, 'M1_C4_P148_R8')
        self.assertTrue(qualification.endswith('_r8.qualification.json'))


if __name__ == '__main__':
    unittest.main()
