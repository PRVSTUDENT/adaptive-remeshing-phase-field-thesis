"""Reusable Mode-I issuer and real embedded gate; all state is temporary."""
import base64,copy,gzip,hashlib,importlib.util,json,sys,unittest,os,tempfile,contextlib,io
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('policy',ROOT/'scripts/hpc/standing_authorization_service.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
sys.path.insert(0,str(Path(__file__).parent))
from test_method_c_batch_gate import BatchGateTests

class ReusableIssuerTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime.now(timezone.utc);self.state={}
  policy.issue_legacy(self.state,{'mode':'enroll'},policy.LEGACY_ISSUER_SHA256,self.now)
  self.state['submission_authorization']={'active':False,'batch_name':'old','consumed':2,'max_submissions':2}
  self.original=copy.deepcopy(self.state)
  policy.issue(self.state,{'mode':'upgrade'},'new-pinned-hash',self.now)
  p=ROOT/'models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/METHOD_C_STAGE_C1_1_AUTHORIZATION.json'
  b=json.loads(p.read_text());h=hashlib.sha256(p.read_bytes()).hexdigest()
  proof=dict(passed=True,pbs_email_verified=True,telegram_verified=True,adapter_contract=policy.GENERIC_ADAPTER,datacheck_verified='PASS_BOTH',checked_at=self.now.isoformat(),candidate_manifest_sha256=h,file_hashes=copy.deepcopy(b['files']),batch_spec_sha256=hashlib.sha256(json.dumps(b,sort_keys=True,separators=(',',':')).encode()).hexdigest(),datachecks={j['id']:dict(status='PASS',input_sha256=b['files'][j['input']],dat_sha256='a'*64) for j in b['jobs']})
  self.request=dict(mode='issue',batch_spec=b,manifest=h,manifest_path=str(p),package_path=str(p.parent),evidence=proof)
 def refresh_spec(self):self.request['evidence']['batch_spec_sha256']=hashlib.sha256(json.dumps(self.request['batch_spec'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 def deny(self):
  self.refresh_spec()
  with self.assertRaises(ValueError):policy.issue(self.state,self.request,'new-pinned-hash',self.now)
 def test_upgrade_keeps_identity_scope_expiry_limits_consumed_permits(self):
  old=self.original['standing_project_authorization'];new=self.state['standing_project_authorization']
  for k in ('grant_id','enrolled_at','scope','expires_at','max_concurrent_jobs','max_replacements_per_chain'):self.assertEqual(old[k],new[k])
  self.assertEqual(self.original['submission_authorization'],self.state['submission_authorization'])
 def test_upgrade_repetition_denied(self):
  with self.assertRaises(ValueError):policy.issue(self.state,{'mode':'upgrade'},'new-pinned-hash',self.now)
 def test_wrong_original_pin_cannot_upgrade(self):
  self.original['standing_project_authorization']['issuer_sha256']='tampered'
  with self.assertRaises(ValueError):policy.issue(self.original,{'mode':'upgrade'},'new-pinned-hash',self.now)
 def test_missing_upgrade_cannot_issue(self):
  with self.assertRaisesRegex(ValueError,'issuer changed'):policy.issue(self.original,self.request,'new-pinned-hash',self.now)
 def test_qualified_p49_derives_two_commands(self):
  policy.issue(self.state,self.request,'new-pinned-hash',self.now);self.assertEqual(self.state['submission_authorization']['max_submissions'],2)
 @unittest.skipUnless(os.name=='posix','Real issuer file lock tested on Linux')
 def test_compressed_cli_upgrade_isolated_state_preserves_counter(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'fixture-state.json';path.write_text(json.dumps(self.original))
   payload=base64.b64encode(gzip.compress(json.dumps({'mode':'upgrade'}).encode())).decode()
   with patch.object(policy,'STATE',str(path)),patch.object(sys,'argv',['issuer',payload,'new-pinned-hash']),contextlib.redirect_stdout(io.StringIO()):policy.main()
   actual=json.loads(path.read_text())
   self.assertEqual(actual['submission_authorization']['consumed'],2)
   self.assertEqual(actual['standing_project_authorization']['issuer_sha256'],'new-pinned-hash')
 def test_future_mode1_manifest_needs_no_package_code_change(self):
  self.request['batch_spec']['batch_name']='MODE1_METHOD_C_STAGE_C1_2';self.request['batch_spec']['technical_stage']='C1-2';self.refresh_spec()
  policy.issue(self.state,self.request,'new-pinned-hash',self.now)
 def test_revocation(self):self.state['standing_project_authorization']['active']=False;self.deny()
 def test_mode2_denied(self):self.request['batch_spec']['scientific_scope']='MODE2';self.deny()
 def test_mpi_denied(self):self.request['batch_spec']['jobs'][0]['execution']='multi-rank MPI';self.deny()
 def test_16_threads_denied(self):self.request['batch_spec']['jobs'][0]['cpus']=16;self.deny()
 def test_large_memory_denied(self):self.request['batch_spec']['jobs'][0]['memory_gb']=32;self.deny()
 def test_shell_injection_denied(self):self.request['batch_spec']['jobs'][0]['command']+='; evil';self.deny()
 def test_path_traversal_denied(self):self.request['batch_spec']['remote_run_dir']+='/../elsewhere';self.deny()
 def test_bad_manifest_binding(self):self.request['evidence']['candidate_manifest_sha256']='wrong';self.deny()
 def test_missing_datacheck_denied(self):self.request['evidence']['datachecks']={};self.deny()
 def test_notification_failure_denied(self):self.request['evidence']['telegram_verified']=False;self.deny()
 def test_duplicate_candidate_cannot_reset(self):
  policy.issue(self.state,self.request,'new-pinned-hash',self.now);self.state['submission_authorization'].update(active=False,consumed=2);self.deny()
 def test_active_partial_permit_is_reused_without_reset(self):
  policy.issue(self.state,self.request,'new-pinned-hash',self.now)
  self.state['submission_authorization']['consumed']=1
  old=copy.deepcopy(self.state['submission_authorization'])
  message=policy.issue(self.state,self.request,'new-pinned-hash',self.now)
  self.assertIn('REUSED',message)
  self.assertEqual(old,self.state['submission_authorization'])
 def test_expired_partial_renewal_keeps_consumption(self):
  policy.issue(self.state,self.request,'new-pinned-hash',self.now)
  self.state['submission_authorization'].update(consumed=1,command_consumption={'equil':1},expires_at='2020-01-01T00:00:00+00:00')
  policy.issue(self.state,self.request,'new-pinned-hash',self.now)
  self.assertEqual(self.state['submission_authorization']['consumed'],1)
  self.assertEqual(self.state['submission_authorization']['command_consumption'],{'equil':1})

class GenericGateTests(BatchGateTests):
 def setUp(self):
  super().setUp()
  self.state['standing_project_authorization']=dict(active=True,grant_id='v2')
  a=self.state['submission_authorization'];a.update(standing_grant_id='v2',max_submissions=2)
  self.manifest.update(adapter=policy.GENERIC_ADAPTER,max_submissions=2,dependency_thresholds={'delta_rf_n':5.,'delta_e_frac_pct':.5},required_state_checks=['state_restoration_verified'])
  self.manifest['jobs']=self.manifest['jobs'][:2];self.manifest['jobs'][1]['depends_on']=['donor']
  self.manifest_path.write_text(json.dumps(self.manifest));self.manifest_hash=hashlib.sha256(self.manifest_path.read_bytes()).hexdigest();a['candidate_manifest_sha256']=self.manifest_hash;a['notification_preflight']['candidate_manifest_sha256']=self.manifest_hash
  self.review=dict(batch_manifest_sha256=self.manifest_hash,scientific_review='PASS',terminal_exit_status=0,reviewed_by='fixture',evidence_report='fixture',evidence_hashes={'odb_extraction':'a'*64},predecessor_pbs_job_id='1415000.mmaster02',metrics={'delta_rf_n':1.,'delta_e_frac_pct':.1},state_checks={'state_restoration_verified':True})
  (self.root/'review.json').write_text(json.dumps(self.review))
 def context(self):
  data=json.loads(gzip.decompress(base64.b64decode(super().context())))
  data['submission_receipts']={'donor':{'pbs_job_id':'1415000.mmaster02'}}
  return base64.b64encode(gzip.compress(json.dumps(data).encode())).decode()
 def test_predecessor_then_reviewed_dependent_once(self):
  self.assertEqual(self.gate(self.commands[1])[0],1)
  self.assertEqual(self.gate(self.commands[0])[0],0)
  self.assertEqual(self.gate(self.commands[1])[0],0)
  self.assertEqual(self.gate(self.commands[1])[0],1)
 def test_missing_state_or_component_metrics_block_forward(self):
  self.assertEqual(self.gate(self.commands[0])[0],0)
  self.review['state_checks']={};(self.root/'review.json').write_text(json.dumps(self.review));self.assertEqual(self.gate(self.commands[1])[0],1)
  self.review['state_checks']={'state_restoration_verified':True};self.review['metrics']={};(self.root/'review.json').write_text(json.dumps(self.review));self.assertEqual(self.gate(self.commands[1])[0],1)
 def test_nonfinite_or_failed_metric_blocks(self):
  self.assertEqual(self.gate(self.commands[0])[0],0)
  for value in (float('nan'),float('inf'),6.):
   self.review['metrics']['delta_rf_n']=value;(self.root/'review.json').write_text(json.dumps(self.review));self.assertEqual(self.gate(self.commands[1])[0],1)
 def test_wrong_pbs_review_blocks(self):
  self.assertEqual(self.gate(self.commands[0])[0],0);self.review['predecessor_pbs_job_id']='1415001.mmaster02';(self.root/'review.json').write_text(json.dumps(self.review));self.assertEqual(self.gate(self.commands[1])[0],1)
 test_donor_once_and_dependencies_fail_without_consuming=None
 test_review_unlocks_two_distinct_recipients_only_once=None
 test_real_lock_prevents_two_simultaneous_donor_consumptions=None

if __name__=='__main__':unittest.main()
