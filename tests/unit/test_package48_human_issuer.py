"""Exercise issuance safeguards on isolated fake state, never real credentials."""
import base64
from datetime import datetime, timezone, timedelta
import json
import importlib.util
import gzip
import hashlib
import subprocess
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ISSUER = Path.home() / 'OpenClawPAD/Set-ControllerAuthorization.ps1'


class IssuerTests(unittest.TestCase):
    def test_transport_executes_only_intact_source(self):
        issuer = ISSUER.read_text(encoding='utf-8-sig')
        transport = re.search(r'\$remote="python3 -c \'(.*?)\'', issuer).group(1)
        body = b"print('VERIFIED_BODY')"
        encoded = base64.b64encode(gzip.compress(body)).decode()
        digest = hashlib.sha256(body).hexdigest()
        for data, expected, accepted in [(encoded, digest, True),
                                         (encoded[:-1], digest, False),
                                         (encoded, '0'*64, False)]:
            result = subprocess.run([sys.executable, '-c', transport, data, expected, 'e30='],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode == 0, accepted)
            self.assertEqual('VERIFIED_BODY' in result.stdout, accepted)

    def test_route_only_or_disabled_queue_refuses_before_notifications(self):
        path = Path(__file__).resolve().parents[2] / 'scripts/hpc/preflight_package48_authorization.py'
        spec = importlib.util.spec_from_file_location('package48_preflight', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for output in ('from_route_only = True\nenabled = True\nstarted = True',
                       'enabled = False\nstarted = True'):
            with patch.object(module.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0, stdout=output)), patch.object(module, 'run_shell') as notifications:
                with self.assertRaises(RuntimeError):
                    module.check({'submission_queue': 'normal_imfdfkmq', 'files': {}})
                notifications.assert_not_called()

    def exercise(self, state, stale=False):
        source = ISSUER.read_text(encoding='utf-8-sig')
        code = re.search(r"\$issue=@'\n(.*?)\n'@", source, re.S).group(1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            path.write_text(json.dumps(state))
            code = code.replace('/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json', str(path).replace('\\', '/'))
            request = dict(batch='MODE1_PACKAGE48_DONOR', command='fixture',
                           command_hash='fixture-hash', manifest='fixture-manifest', hours=24,
                           evidence={'checked_at': (datetime.now(timezone.utc)-timedelta(minutes=10 if stale else 0)).isoformat()})
            fake = types.SimpleNamespace(LOCK_EX=1, flock=lambda *args: None)
            encoded = base64.b64encode(json.dumps(request).encode()).decode()
            try:
                with patch.dict(sys.modules, {'fcntl': fake}), patch.object(sys, 'argv', ['test', encoded]):
                    exec(compile(code, 'isolated-issuer-test', 'exec'), {})
                failure = None
            except SystemExit as error:
                failure = str(error)
            return json.loads(path.read_text()), failure

    def test_new_permit_preserves_old_counters_in_history(self):
        old = dict(active=False, consumed=2, max_submissions=2, batch_name='OLDER_BATCH')
        state, failure = self.exercise({'submission_authorization': old})
        self.assertIsNone(failure)
        self.assertEqual(state['submission_authorization_history'], [old])
        self.assertEqual(state['submission_authorization']['max_submissions'], 1)

    def test_active_duplicate_and_stale_refuse_without_state_changes(self):
        for old, stale in [(dict(active=True), False),
                           (dict(active=False, batch_name='MODE1_PACKAGE48_DONOR', consumed=1), False),
                           (dict(active=False, consumed=2), True)]:
            original = {'submission_authorization': old}
            state, failure = self.exercise(original, stale)
            self.assertIsNotNone(failure)
            self.assertEqual(state, original)

    def test_historical_batch_cannot_be_reissued(self):
        original = {'submission_authorization_history': [{'batch_name': 'MODE1_PACKAGE48_DONOR'}]}
        state, failure = self.exercise(original)
        self.assertIsNotNone(failure)
        self.assertEqual(state, original)


if __name__ == '__main__':
    unittest.main()
