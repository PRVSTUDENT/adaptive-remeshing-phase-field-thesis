"""Active technical gate regression tests. No scheduler, network or credentials."""
import copy,hashlib,importlib.util,json,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('execution',ROOT/'scripts/hpc/mode1_execution_gate.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)

class ExecutionGateTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  p=self.root/'models/pandey_kumar_mode1/fixture';p.mkdir(parents=True)
  source=ROOT/'models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer'
  self.batch=json.loads((source/'METHOD_C_STAGE_C1_1_AUTHORIZATION.json').read_text(encoding='utf-8-sig'))
  for name in self.batch['files']:
   content=(source/name).read_bytes() if name=='f42_mixed_uel.for' else ('fixture '+name).encode()
   (p/name).write_bytes(content);self.batch['files'][name]=engine.digest(content)
  self.path=p/'batch.json';self.refresh()
 def refresh(self):
  self.path.write_text(json.dumps(self.batch),encoding='utf-8');self.key=engine.digest(self.path.read_bytes())
  self.proof={'passed':True,'pbs_email_verified':True,'telegram_verified':True,'active_job_count':0,'candidate_manifest_sha256':self.key,'file_hashes':copy.deepcopy(self.batch['files']),'batch_spec_sha256':engine.digest(json.dumps(self.batch,sort_keys=True,separators=(',',':')).encode()),'checked_at':datetime.now(timezone.utc).isoformat(),'datachecks':{j['id']:{'status':'PASS','input_sha256':self.batch['files'][j['input']],'dat_sha256':'a'*64} for j in self.batch['jobs']}}
  self.request={'manifest_path':str(self.path),'preflight':self.proof}
 def prepare(self):return engine.prepare(self.request,self.root)
 def receipt(self):
  f=self.root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json';f.parent.mkdir(parents=True,exist_ok=True)
  f.write_text(json.dumps({self.key:{'equil_test':{'pbs_job_id':'1414235.mmaster02','command_sha256':self.batch['jobs'][0]['command_sha256']}}}))
 def review(self):
  r={'batch_manifest_sha256':self.key,'scientific_review':'PASS','terminal_exit_status':0,'reviewed_by':'fixture','evidence_report':'fixture','predecessor_pbs_job_id':'1414235.mmaster02','evidence_hashes':{'actual_state':'b'*64},'metrics':{n:0 for n in self.batch['dependency_thresholds']},'state_checks':{n:True for n in self.batch['required_state_checks']}}
  f=self.root/self.batch['dependency_review_path'];f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(r));return r,f
 def test_no_authorization_or_grant_needed(self):
  self.prepare();engine.reserve(self.batch['jobs'][0]['command'],self.root)
  self.assertEqual(engine.status(self.key,self.root)['attempts']['equil_test'],1)
 def test_existing_receipt_imported_without_rerunning(self):
  self.receipt();self.prepare()
  self.assertNotIn('equil_test',engine.status(self.key,self.root)['ready_jobs'])
  with self.assertRaisesRegex(ValueError,'already submitted'):engine.reserve(self.batch['jobs'][0]['command'],self.root)
 def test_duplicate_denied(self):
  self.prepare();engine.reserve(self.batch['jobs'][0]['command'],self.root)
  with self.assertRaises(ValueError):engine.reserve(self.batch['jobs'][0]['command'],self.root)
 def test_preflight_refresh_does_not_reset_attempts(self):
  self.prepare();engine.reserve(self.batch['jobs'][0]['command'],self.root);self.prepare()
  self.assertEqual(engine.status(self.key,self.root)['attempts']['equil_test'],1)
 def test_atomic_parallel_duplicate_only_once(self):
  self.prepare()
  def call(_):
   try:engine.reserve(self.batch['jobs'][0]['command'],self.root);return True
   except ValueError:return False
  with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(sorted(pool.map(call,range(2))),[False,True])
 def test_arbitrary_command_denied(self):
  self.prepare()
  with self.assertRaises(ValueError):engine.reserve('qsub evil.pbs',self.root)
 def test_changed_input_denied(self):
  self.prepare();(self.path.parent/self.batch['jobs'][0]['input']).write_text('tampered')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):engine.reserve(self.batch['jobs'][0]['command'],self.root)
 def test_mpi_resource_expansion_denied(self):
  self.batch['jobs'][0]['cpus']=16;self.refresh()
  with self.assertRaisesRegex(ValueError,'Resource'):self.prepare()
 def test_memory_expansion_denied(self):
  self.batch['jobs'][0]['memory_gb']=32;self.refresh()
  with self.assertRaises(ValueError):self.prepare()
 def test_wrong_scope_denied(self):
  self.batch['scientific_scope']='MODE2';self.refresh()
  with self.assertRaises(ValueError):self.prepare()
 def test_missing_real_notification_denied(self):
  self.proof['telegram_verified']=False
  with self.assertRaisesRegex(ValueError,'notification'):self.prepare()
 def test_unbound_datacheck_denied(self):
  self.proof['datachecks']['equil_test']['input_sha256']='bad'
  with self.assertRaisesRegex(ValueError,'datacheck'):self.prepare()
 def test_additional_phase_datacheck_required(self):
  self.batch['jobs'][0]['additional_datachecks']=['phase.dat']
  (self.path.parent/'phase.inp').write_bytes(b'phase fixture')
  self.batch['files']['phase.inp']=engine.digest(b'phase fixture');self.refresh()
  with self.assertRaisesRegex(ValueError,'Additional input-bound'):self.prepare()
  self.proof['datachecks']['equil_test']['additional']={'phase.dat':{'status':'PASS','input_sha256':self.batch['files']['phase.inp'],'dat_sha256':'b'*64}}
  self.prepare()
  self.proof['datachecks']['equil_test']['additional']['phase.dat']['input_sha256']='c'*64
  with self.assertRaisesRegex(ValueError,'Additional input-bound'):self.prepare()
 def test_stale_technical_preflight_requires_refresh(self):
  self.proof['checked_at']=(datetime.now(timezone.utc)-timedelta(minutes=6)).isoformat()
  with self.assertRaisesRegex(ValueError,'Refresh technical'):self.prepare()
 def test_missing_scientific_review_blocks_forward(self):
  self.receipt();self.prepare()
  with self.assertRaisesRegex(ValueError,'scientific review pending'):engine.reserve(self.batch['jobs'][1]['command'],self.root)
 def test_failed_scientific_review_blocks_forward(self):
  self.receipt();self.prepare();r,f=self.review();r['scientific_review']='FAIL';f.write_text(json.dumps(r))
  with self.assertRaisesRegex(ValueError,'has not passed'):engine.reserve(self.batch['jobs'][1]['command'],self.root)
 def test_actual_pass_review_allows_forward_once(self):
  self.receipt();self.prepare();self.review();engine.reserve(self.batch['jobs'][1]['command'],self.root)
  with self.assertRaises(ValueError):engine.reserve(self.batch['jobs'][1]['command'],self.root)
 def test_zero_missing_state_cannot_pass(self):
  self.receipt();self.prepare();r,f=self.review();r['state_checks']={};f.write_text(json.dumps(r))
  with self.assertRaisesRegex(ValueError,'State preservation'):engine.reserve(self.batch['jobs'][1]['command'],self.root)
 def test_nonfinite_or_excess_energy_blocks(self):
  self.receipt();self.prepare();r,f=self.review()
  for value in (float('nan'),1.):
   r['metrics']['delta_e_tot_pct']=value;f.write_text(json.dumps(r))
   with self.assertRaisesRegex(ValueError,'quantitative'):engine.reserve(self.batch['jobs'][1]['command'],self.root)
 def test_wrong_actual_pbs_blocks(self):
  self.receipt();self.prepare();r,f=self.review();r['predecessor_pbs_job_id']='999.mmaster02';f.write_text(json.dumps(r))
  with self.assertRaisesRegex(ValueError,'PBS receipt'):engine.reserve(self.batch['jobs'][1]['command'],self.root)
 def test_four_job_capacity_blocks(self):
  self.proof['active_job_count']=4
  with self.assertRaisesRegex(ValueError,'resource count'):self.prepare()
 def test_experimental_offset_configuration_allowed(self):
  exp_batch=copy.deepcopy(self.batch)
  exp_batch['adapter']='mode1-experimental-offset-v1'
  exp_batch['technical_stage']='EXPERIMENTAL_OFFSET'
  exp_batch['hypothesis']='Guarded extrapolation=NO resolves continuation discrepancy'
  del exp_batch['files']['f42_mixed_uel.for']
  exp_uel_content=(ROOT/'models/pandey_kumar_mode1/experimental_offset_uel/f42_experimental_offset_uel.for').read_bytes()
  (self.path.parent/'f42_experimental_offset_uel.for').write_bytes(exp_uel_content)
  exp_batch['files']['f42_experimental_offset_uel.for']=engine.digest(exp_uel_content)
  self.batch=exp_batch
  self.refresh()
  self.prepare()
  engine.reserve(self.batch['jobs'][0]['command'],self.root)
  self.assertEqual(engine.status(self.key,self.root)['attempts']['equil_test'],1)
 def test_experimental_offset_without_hypothesis_denied(self):
  exp_batch=copy.deepcopy(self.batch)
  exp_batch['adapter']='mode1-experimental-offset-v1'
  exp_batch['technical_stage']='EXPERIMENTAL_OFFSET'
  del exp_batch['files']['f42_mixed_uel.for']
  exp_uel_content=(ROOT/'models/pandey_kumar_mode1/experimental_offset_uel/f42_experimental_offset_uel.for').read_bytes()
  (self.path.parent/'f42_experimental_offset_uel.for').write_bytes(exp_uel_content)
  exp_batch['files']['f42_experimental_offset_uel.for']=engine.digest(exp_uel_content)
  self.batch=exp_batch
  self.refresh()
  with self.assertRaisesRegex(ValueError,'hypothesis'):self.prepare()
 def test_experimental_offset_tampered_uel_denied(self):
  exp_batch=copy.deepcopy(self.batch)
  exp_batch['adapter']='mode1-experimental-offset-v1'
  exp_batch['technical_stage']='EXPERIMENTAL_OFFSET'
  exp_batch['hypothesis']='Testing'
  del exp_batch['files']['f42_mixed_uel.for']
  tampered=b'tampered experimental uel'
  (self.path.parent/'f42_experimental_offset_uel.for').write_bytes(tampered)
  exp_batch['files']['f42_experimental_offset_uel.for']=engine.digest(tampered)
  self.batch=exp_batch
  self.refresh()
  with self.assertRaisesRegex(ValueError,'Experimental offset UEL'):self.prepare()

if __name__=='__main__':unittest.main()
