"""Synthetic OAuth/client fixtures. No account files, network or secrets."""
import importlib.util
import sys
import types
from pathlib import Path
import unittest
from unittest.mock import patch


def worker():
    pkg=types.ModuleType('ai_limit_checker');ag=types.ModuleType('ai_limit_checker.antigravity')
    ag.check_antigravity=lambda _:None;ag.TOKEN_URL='https://oauth.invalid/token';pkg.antigravity=ag
    cred=types.ModuleType('ai_limit_checker.credentials');cred.parse_windows_blob=lambda b:b
    spec=importlib.util.spec_from_file_location('fixture_quota',Path(__file__).resolve().parents[2]/'scripts/validation/agy_saved_profile_quota.py')
    mod=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'ai_limit_checker':pkg,'ai_limit_checker.antigravity':ag,'ai_limit_checker.credentials':cred}):spec.loader.exec_module(mod)
    return mod


class RefreshTests(unittest.TestCase):
    def setUp(self):self.w=worker();self.identity=self.w.canonical_identity('fixture-subject')
    def provider(self,*args,**kw):return 200,{'sub':'fixture-subject'}
    def test_wrong_embedded_pair_then_valid_refresh(self):
        calls=[]
        def form(url,data):
            calls.append(data['client_secret'])
            return (401,{'error':'invalid_client'}) if len(calls)==1 else (200,{'access_token':'FAKE_ACCESS'})
        access=self.w.refresh_with_candidates('FAKE_GRANT','FAKE_CLIENT',['wrong','matching'],self.identity,form,self.provider)
        self.assertEqual(access,'FAKE_ACCESS');self.assertEqual(calls,['wrong','matching'])
    def test_failed_grant_does_not_try_more_clients(self):
        calls=[]
        def form(*args):calls.append(1);return 400,{'error':'invalid_grant'}
        with self.assertRaisesRegex(RuntimeError,'AUTHENTICATION_FAILED'):
            self.w.refresh_with_candidates('fake','fake',['one','two'],self.identity,form,self.provider)
        self.assertEqual(len(calls),1)
    def test_refreshed_identity_mismatch_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'PROVIDER_IDENTITY_MISMATCH'):
            self.w.refresh_with_candidates('fake','fake',['one'],self.identity,lambda *a:(200,{'access_token':'fake'}),lambda *a,**k:(200,{'sub':'different'}))
    def test_all_invalid_clients_stays_unknown(self):
        with self.assertRaisesRegex(RuntimeError,'OAUTH_CLIENT_REJECTED'):
            self.w.refresh_with_candidates('fake','fake',['one','two'],self.identity,lambda *a:(401,{'error':'invalid_client'}),self.provider)
    def test_valid_cached_profile_identity(self):self.w.verify_provider_identity('FAKE',self.identity,self.provider)
    def test_exhausted_quota_is_valid_zero(self):
        self.w.antigravity._parse_bucket=lambda b:{'remaining_fraction':0}
        self.w.install_quota_repair()
        result=self.w.antigravity._parse_bucket({'window':'weekly'})
        self.assertEqual(result['remaining_pct'],0)
        self.assertEqual(result['used_pct'],100)
    def test_provider_unavailable_is_not_zero_quota(self):
        with self.assertRaisesRegex(RuntimeError,'PROVIDER_IDENTITY_UNAVAILABLE'):
            self.w.verify_provider_identity('FAKE',self.identity,lambda *a,**k:(503,{}))
