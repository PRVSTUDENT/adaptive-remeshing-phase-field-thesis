"""Credential identity compatibility using synthetic values only; no login/HTTP."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch


def load_worker():
    fake = types.ModuleType('ai_limit_checker')
    ag = types.ModuleType('ai_limit_checker.antigravity')
    ag.check_antigravity = lambda _: (_ for _ in ()).throw(AssertionError('HTTP forbidden'))
    fake.antigravity = ag
    creds = types.ModuleType('ai_limit_checker.credentials')
    creds.parse_windows_blob = lambda b: json.loads(b)['token']
    path = Path(os.environ['USERPROFILE'])/'OpenClawPAD/agy_profile_quota.py'
    spec = importlib.util.spec_from_file_location('quota_identity_fixture', path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'ai_limit_checker': fake,
                                 'ai_limit_checker.antigravity': ag,
                                 'ai_limit_checker.credentials': creds}):
        spec.loader.exec_module(module)
    return module


def jwt(subject):
    encoded = base64.urlsafe_b64encode(json.dumps({'sub': subject}).encode()).decode().rstrip('=')
    return 'fixture.'+encoded+'.signature'


def envelope(data):
    return {'blobB64': base64.b64encode(json.dumps(data).encode()).decode()}


class IdentityCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = load_worker()

    def test_root_nested_and_legacy_layouts_agree(self):
        first = jwt('fixture-a')
        for data in ({'token': {'refresh_token': 'FAKE'}, 'id_token': first},
                     {'token': {'refresh_token': 'FAKE', 'id_token': first}},
                     {'refresh_token': 'FAKE', 'id_token': first}):
            with self.subTest(layout=data):
                blob, identity, _ = self.worker.inspect(envelope(data))
                self.assertEqual(identity, hashlib.sha256(b'fixture-a').hexdigest()[:16])
                self.assertEqual(json.loads(blob)['token']['refresh_token'], 'FAKE')

    def test_real_mismatch_and_missing_metadata_rejected(self):
        for data in ({'token': {'refresh_token': 'FAKE', 'id_token': jwt('fixture-b')},
                      'id_token': jwt('fixture-a')},
                     {'token': {'refresh_token': 'FAKE'}},
                     {'token': {'id_token': jwt('fixture-a')}}):
            with self.subTest(layout=data), self.assertRaises(ValueError):
                self.worker.inspect(envelope(data))

    def test_canonicalization_is_exact_and_validates_subject_type(self):
        for subject in ('fixture-a', 'Fixture-A', ' fixture-a ', '\u00e9\u03a9'):
            self.assertEqual(self.worker.canonical_identity(subject),
                             hashlib.sha256(subject.encode('utf-8')).hexdigest()[:16])
        for bad in (None, '', ' ', 123, True, ['fixture-a']):
            with self.subTest(subject=bad), self.assertRaises(ValueError):
                self.worker.canonical_identity(bad)

    def test_powershell_and_python_identity_vectors_match(self):
        root = Path(__file__).resolve().parents[2]
        helper = (root/'scripts/validation/AgyCredentialStores.ps1').as_posix()
        subjects = ['fixture-a', 'Fixture-A', ' fixture-a ', '\u00e9\u03a9']
        encoded = base64.b64encode(json.dumps(subjects).encode()).decode()
        code = (". '"+helper+"'; $items=[Text.Encoding]::UTF8.GetString("
                "[Convert]::FromBase64String('"+encoded+"'))|ConvertFrom-Json; "
                "@($items|ForEach-Object{Get-AgyCanonicalIdentity -Subject $_})|ConvertTo-Json -Compress")
        result = subprocess.run(['powershell', '-NoProfile', '-Command', code],
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=20, check=True)
        self.assertEqual(json.loads(result.stdout),
                         [self.worker.canonical_identity(s) for s in subjects])


if __name__ == '__main__':
    unittest.main()
