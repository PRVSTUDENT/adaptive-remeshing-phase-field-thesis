"""Quota parity regression tests; synthetic replies and no credentials."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('worker', Path.home() / 'OpenClawPAD/agy_profile_quota.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

class QuotaParityTests(unittest.TestCase):
    def setUp(self):
        self.old = worker.antigravity._parse_bucket
        worker.install_quota_repair()
        self.addCleanup(setattr, worker.antigravity, '_parse_bucket', self.old)

    def test_cli_user_agent(self):
        self.assertIn('antigravity/cli/', worker.antigravity.USER_AGENT)
        self.assertIn('aidev_client', worker.antigravity.USER_AGENT)

    def test_cli_precision(self):
        b = worker.antigravity._parse_bucket({'remainingFraction': .5464821, 'window': 'weekly'})
        self.assertEqual(b['remaining_pct'], 54.65)

    def test_disabled_is_unavailable(self):
        b = worker.antigravity._parse_bucket({'disabled': True, 'remainingFraction': 1, 'window': '5h'})
        self.assertIsNone(b['remaining_pct'])
        self.assertEqual(b['status'], 'NONAPPLICABLE')

    def test_missing_fraction_not_invented(self):
        self.assertIsNone(worker.antigravity._parse_bucket({'window': '5h'}))

    def test_missing_gemini_not_supplemented(self):
        data = {'groups': [{'displayName': 'Claude and GPT models', 'buckets': [{'remainingFraction': 1}]}]}
        with patch.object(worker.antigravity.utils, 'http_json', return_value=(200, data)) as api:
            result = worker.antigravity.fetch_quota_summary('synthetic', None)
        self.assertEqual(result, data)
        self.assertEqual(api.call_count, 1)
        self.assertIn('daily-cloudcode-pa.googleapis.com', api.call_args.args[1])

    def test_invalid_fraction_rejected(self):
        with self.assertRaises(ValueError):
            worker.antigravity._parse_bucket({'remainingFraction': 1.2})

if __name__ == '__main__':
    unittest.main()
