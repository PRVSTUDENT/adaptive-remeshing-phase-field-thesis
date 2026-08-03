import json,os,subprocess,tempfile,unittest
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
class F21Preparation(unittest.TestCase):
 def text(self,p): return open(os.path.join(ROOT,p),encoding='utf-8').read()
 def test_single_route_no_fallback(self):
  s=self.text('models/generated/mode_ii/f21_native_remesh_execution/runtime/execute_f21_native_remesh.py')
  self.assertEqual(s.count('model.adaptiveRemesh(odb)'),1); self.assertNotIn('AdaptivityProcess(',s)
 def test_downstream_counters_zero(self):
  d=json.loads(self.text('models/generated/mode_ii/f21_native_remesh_execution/F21_NO_EXECUTION_AUDIT.json'))
  for k in ('solver_executions','datacheck_executions','state_transfer_executions','refined_analyses','qsub_attempts'): self.assertEqual(d[k],0)
 def test_candidate_and_source_contract(self):
  s=self.text('models/generated/mode_ii/f21_native_remesh_execution/runtime/execute_f21_native_remesh.py')
  self.assertIn('M2RMEXEC1_candidate.inp',s); self.assertIn('bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac',s)
 def test_orchestrator_one_call_explicit_vars(self):
  s=self.text('scripts/hpc/stage_f/submit_stage_f21_native_remesh.sh')
  self.assertEqual(s.count('qsub -v'),1); self.assertNotIn('qsub -V',s); self.assertIn('F21_PACKAGE_DIR=${package},F21_EVIDENCE_DIR=${evidence}',s)
 def test_classifications(self):
  s=self.text('models/generated/mode_ii/f21_native_remesh_execution/runtime/execute_f21_native_remesh.py')
  for c in ('native_remesh_candidate_generated_pending_datacheck','native_remesh_completed_without_mesh_change','native_remesh_api_execution_failed','native_remesh_source_integrity_failed','native_remesh_candidate_integrity_failed','native_remesh_slit_topology_failed'): self.assertIn(c,s)
if __name__=='__main__': unittest.main()
