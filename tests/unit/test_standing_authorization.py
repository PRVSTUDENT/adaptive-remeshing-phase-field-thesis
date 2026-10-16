"""Standing issuer and actual embedded gate security regression; no PBS submissions."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('standing',ROOT/'scripts/hpc/standing_authorization_service.py')
service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
sys.path.insert(0,str(Path(__file__).parent))
from test_method_c_batch_gate import BatchGateTests

class StandingIssuerTests(unittest.TestCase):
 def setUp(self):
  self.state={}
  self.now=datetime.now(timezone.utc)
  service.issue(self.state,{'mode':'enroll'},'pinned',self.now)
  p=ROOT/'models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control'
  b=json.loads((p/'METHOD_C_RESTART_RECOVERY_AUTHORIZATION.json').read_text())
  h=hashlib.sha256((p/'METHOD_C_RESTART_RECOVERY_AUTHORIZATION.json').read_bytes()).hexdigest()
  self.request=dict(mode='issue',batch_spec=b,manifest=h,manifest_path='batch.json',package_path='package',evidence=dict(passed=True,pbs_email_verified=True,telegram_verified=True,checked_at=self.now.isoformat(),candidate_manifest_sha256=h,file_hashes=b['files'],restart_datacheck='PASS_BOTH',checkpoint_hashes=b['checkpoint_hashes']))
 def deny(self):
  with self.assertRaises(ValueError):service.issue(self.state,self.request,'pinned',self.now)
 def test_two_separately_validated_commands(self):
  service.issue(self.state,self.request,'pinned',self.now)
  a=self.state['submission_authorization'];self.assertEqual(len(a['authorized_commands']),2);self.assertEqual(a['max_submissions'],2)
  self.assertIsNone(self.state['standing_project_authorization']['expires_at'])
 def test_expired_partial_permit_renews_without_reset(self):
  service.issue(self.state,self.request,'pinned',self.now)
  a=self.state['submission_authorization'];a.update(consumed=1,expires_at='2020-01-01T00:00:00+00:00',command_consumption={'prod':1})
  service.issue(self.state,self.request,'pinned',self.now)
  self.assertEqual(self.state['submission_authorization']['consumed'],1)
  self.assertEqual(self.state['submission_authorization']['command_consumption'],{'prod':1})
 def test_unenrolled(self):self.state={};self.deny()
 def test_revoked(self):self.state['standing_project_authorization']['active']=False;self.deny()
 def test_issuer_tampering(self):
  with self.assertRaises(ValueError):service.issue(self.state,self.request,'changed',self.now)
 def test_reenrollment_denied(self):
  with self.assertRaises(ValueError):service.issue(self.state,{'mode':'enroll'},'pinned',self.now)
 def test_repeat_candidate_denied(self):
  service.issue(self.state,self.request,'pinned',self.now);a=self.state['submission_authorization'];a.update(active=False,consumed=2);self.deny();self.assertEqual(a['consumed'],2)
 def test_new_manifest_cannot_reset_retry_chain(self):
  service.issue(self.state,self.request,'pinned',self.now);self.state['submission_authorization'].update(active=False,consumed=2);self.request['manifest']='new';self.request['evidence']['candidate_manifest_sha256']='new';self.deny()
 def test_unvalidated(self):self.request['evidence']['restart_datacheck']='UNRESOLVED';self.deny()
 def test_missing_notification(self):self.request['evidence']['telegram_verified']=False;self.deny()
 def test_expired_preflight(self):self.request['evidence']['checked_at']='2020-01-01T00:00:00+00:00';self.deny()
 def test_resource_expansion(self):self.request['batch_spec']['jobs'][0]['cpus']=16;self.deny()
 def test_arbitrary_command(self):self.request['batch_spec']['jobs'][0]['command']='qsub evil.pbs';self.deny()
 def test_wrong_scope(self):self.request['batch_spec']['adapter']='MODE2';self.deny()
 def test_unreviewed_checkpoint(self):self.request['batch_spec']['scientific_review']='UNRESOLVED';self.deny()
 def test_changed_uel(self):self.request['batch_spec']['files']['f42_mixed_uel.for']='changed';self.deny()

class StandingGateTests(BatchGateTests):
 def setUp(self):
  super().setUp()
  self.state['standing_project_authorization']=dict(active=True,grant_id='grant')
  self.state['submission_authorization']['standing_grant_id']='grant'
  self.state['submission_authorization']['max_submissions']=2
  self.manifest['max_submissions']=2
  self.manifest['jobs']=self.manifest['jobs'][1:]
  self.manifest['donor_pbs_job_id']='1413814.mmaster02'
  self.review=dict(batch_manifest_sha256='',donor_terminal_exit_status=0,checkpoint_verified=True,scientific_review='PASS',handoff_displacement_mm=0.005,donor_pbs_job_id='1413814.mmaster02',checkpoint_hashes={'checkpoint.res':'a'*64},reviewed_by='fixture',evidence_report='fixture')
  self.manifest['checkpoint_hashes']=self.review['checkpoint_hashes']
  self.manifest_path.write_text(json.dumps(self.manifest))
  self.manifest_hash=hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
  a=self.state['submission_authorization'];a['candidate_manifest_sha256']=self.manifest_hash;a['notification_preflight']['candidate_manifest_sha256']=self.manifest_hash
  self.review['batch_manifest_sha256']=self.manifest_hash
  (self.root/'review.json').write_text(json.dumps(self.review))
 def test_standing_recipients_once_each(self):
  self.assertEqual(self.gate(self.commands[1])[0],0)
  self.assertEqual(self.gate(self.commands[1])[0],1)
  self.assertEqual(self.gate(self.commands[2])[0],0)
  self.assertEqual(self.gate(self.commands[2])[0],1)
 def test_revocation_invalidates_existing_permit(self):
  self.state['standing_project_authorization']['active']=False
  self.assertEqual(self.gate(self.commands[1])[0],1)
 # Base batch tests are exercised separately with original three-job fixtures.
 test_donor_once_and_dependencies_fail_without_consuming=None
 test_review_unlocks_two_distinct_recipients_only_once=None
 test_real_lock_prevents_two_simultaneous_donor_consumptions=None

if __name__=='__main__':unittest.main()
