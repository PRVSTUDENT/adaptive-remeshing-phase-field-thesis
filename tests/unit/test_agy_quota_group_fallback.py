"""Exercise the installed quota adapter with synthetic API replies, no credentials."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

try:
    spec = importlib.util.spec_from_file_location('agy_worker', Path.home() / 'OpenClawPAD/agy_profile_quota.py')
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
except (ImportError, FileNotFoundError) as error:
    raise unittest.SkipTest('Installed Antigravity quota worker/dependencies required') from error


class QuotaGroupFallbackTests(unittest.TestCase):
    def setUp(self):
        self.primary = {'groups': [{'displayName': 'Claude and GPT models', 'buckets': [{'remainingFraction': .25}]}]}
        self.first = patch.object(worker.antigravity, 'fetch_quota_summary', return_value=self.primary)
        self.first.start(); self.addCleanup(self.first.stop)
        self.http = patch.object(worker.antigravity.utils, 'http_json')
        self.api = self.http.start(); self.addCleanup(self.http.stop)
        worker.install_quota_group_fallback()

    def test_supplements_actual_missing_gemini_group(self):
        gemini = {'displayName': 'Gemini Models', 'buckets': [{'remainingFraction': .877}]}
        self.api.return_value = (200, {'groups': [gemini, {'displayName': 'Claude and GPT models'}]})
        result = worker.antigravity.fetch_quota_summary('synthetic-token', 'synthetic-project')
        self.assertEqual(result['groups'], self.primary['groups'] + [gemini])
        self.assertEqual(self.primary['groups'][0]['buckets'][0]['remainingFraction'], .25)
        self.assertIn('cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary', self.api.call_args.args[1])

    def test_primary_gemini_is_authoritative_no_extra_request(self):
        self.primary['groups'].append({'displayName': 'Gemini Models', 'buckets': []})
        self.assertEqual(worker.antigravity.fetch_quota_summary('synthetic', None), self.primary)
        self.api.assert_not_called()

    def test_failure_does_not_invent_gemini_capacity(self):
        self.api.return_value = (503, {})
        self.assertEqual(worker.antigravity.fetch_quota_summary('synthetic', None), self.primary)

    def test_401_enters_existing_bounded_refresh_path(self):
        self.api.return_value = (401, {})
        with self.assertRaisesRegex(RuntimeError, 'HTTP 401'):
            worker.antigravity.fetch_quota_summary('synthetic', None)

    def test_duplicate_groups_not_appended(self):
        self.api.return_value = (200, {'groups': [{'displayName': 'Gemini Models'}, {'displayName': 'Gemini Models'}]})
        result = worker.antigravity.fetch_quota_summary('synthetic', None)
        self.assertEqual(len(result['groups']), 2)

    def test_empty_secondary_remains_unknown(self):
        self.api.return_value = (200, {'groups': []})
        self.assertEqual(worker.antigravity.fetch_quota_summary('synthetic', None), self.primary)


if __name__ == '__main__':
    unittest.main()
