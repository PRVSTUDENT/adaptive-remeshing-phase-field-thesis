import hashlib, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/"runs/hpc/stage_f/f15_f16_conditional_batch_preparation"
INF=ROOT/"models/generated/infrastructure/f15_dual_channel_notification_smoke"
CTL=ROOT/"models/generated/mode_ii/f16_controlled_rollback_control"
FORCE=ROOT/"models/generated/mode_ii/f16_controlled_rollback_forced"
REG=ROOT/"models/generated/mode_ii/f16_native_adaptive_region_resolution"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

class ConditionalBatchTests(unittest.TestCase):
 def test_allowlist_waves_and_limits(self):
  d=json.loads((RUN/"CONDITIONAL_BATCH_PLAN.json").read_text())
  self.assertEqual(d["jobs"],["M2NOTIFY1","M2IRRROLLCTL2","M2IRRROLLFORCE2","M2RMREG2"])
  self.assertEqual(d["wave_a"],["M2NOTIFY1"]); self.assertEqual(len(d["wave_b"]),3)
  self.assertEqual(d["maximum_qsub_attempts"],4); self.assertEqual(d["maximum_running_jobs"],2)
  self.assertFalse(d["retry"]); self.assertFalse(d["replacement"]); self.assertFalse(d["direct_qsub"])
 def test_wave_b_human_gate(self):
  d=json.loads((RUN/"CONDITIONAL_BATCH_DEPENDENCIES.json").read_text())
  self.assertEqual(len(d["wave_b_gate"]["human_confirmations"]),4)
 def test_no_authority_or_execution(self):
  d=json.loads((RUN/"NO_UNAUTHORIZED_EXECUTION_AUDIT.json").read_text())
  self.assertFalse(d["execution_authorized"]); self.assertFalse(d["submission_approved"])
  self.assertEqual((d["qsub_attempts"],d["maximum_jobs_now"]),(0,0))
 def test_pbs_email_and_telegram_hooks(self):
  for p in (next(INF.glob('*.pbs')),next(CTL.glob('*.pbs')),next(FORCE.glob('*.pbs')),next(REG.glob('*.pbs'))):
   s=p.read_text(); self.assertIn("#PBS -m abe",s)
   self.assertIn("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de",s)
   self.assertIn("notify_start",s); self.assertIn("notification_install_terminal_trap",s)
   self.assertNotIn("qsub ",s); self.assertIn('${SCRATCH:?SCRATCH is required}',s)
 def test_notification_portability_and_redaction(self):
  s=(ROOT/"scripts/hpc/notifications/job_notifications.sh").read_text()
  self.assertNotIn("--fail-with-body",s); self.assertIn("native_pbs",s)
  for p in [INF,CTL,FORCE,REG,RUN]:
   for f in p.rglob('*'):
    if f.is_file():
     t=f.read_text(errors='ignore'); self.assertNotRegex(t,r"bot\d+:[A-Za-z0-9_-]{20,}")
 def test_smoke_is_shell_only(self):
  s=(INF/"M2NOTIFY1.pbs").read_text().lower(); self.assertNotIn("module load",s); self.assertNotIn("abaqus job=",s); self.assertIn("sleep 30",s)
 def test_rollback_identity_and_runtime_only_difference(self):
  for f in ("runtime/M2IRR_F16.inp","runtime/M2IRR_F16.for"):
   self.assertEqual((CTL/f).read_bytes(),(FORCE/f).read_bytes())
  a=json.loads((CTL/"PACKAGE_MANIFEST.json").read_text()); b=json.loads((FORCE/"PACKAGE_MANIFEST.json").read_text())
  self.assertEqual(a["source_sha256"],b["source_sha256"]); self.assertEqual(a["deck_sha256"],b["deck_sha256"])
  self.assertEqual((a["f16_force_cutback"],b["f16_force_cutback"]),(0,1))
 def test_fortran_runtime_trigger_and_logging(self):
  s=(CTL/"runtime/M2IRR_F16.for").read_text().upper()
  self.assertIn("CALL GETOUTDIR",s); self.assertIn("CALL GETJOBNAME",s)
  self.assertNotIn("GET_ENVIRONMENT_VARIABLE",s); self.assertNotIn("FOR_GETENV_ERR",s); self.assertNotIn("SAVE",s)
  self.assertIn("PNEWDT=HALF",s); self.assertIn("F16_CALL",s); self.assertIn("USRVAR(JELEM,16",s)
 def test_response_tolerances_and_independent_solver_evidence(self):
  m=json.loads((FORCE/"PACKAGE_MANIFEST.json").read_text()); self.assertTrue(m["independent_sta_msg_evidence_required"])
  self.assertEqual(m["tolerances"]["displacement_mm"],1e-10); self.assertEqual(m["tolerances"]["rf_u_nrmse"],1e-4)
 def test_remesh_official_hashes_and_zero_execution(self):
  m=json.loads((REG/"PACKAGE_MANIFEST.json").read_text()); self.assertEqual(m["deck_sha256"],"a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2")
  self.assertEqual(m["odb_sha256"],"bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac")
  self.assertEqual((m["solver_executions"],m["native_remesh_calls"],m["generated_candidates"]),(0,0,0))
  s=(REG/"runtime/qualify_f16_adaptive_region.py").read_text(); self.assertIn("Part2DGeomFrom2DMesh",s)
  self.assertNotIn(".adaptiveRemesh(",s); self.assertNotIn(".submit(",s); self.assertIn("ALE_adaptive_meshing",s)
 def test_json_and_hash_manifests(self):
  for root in (INF,CTL,FORCE,REG,RUN):
   for f in root.rglob('*.json'): json.loads(f.read_text())
  for p in (INF,CTL,FORCE,REG):
   for line in (p/"SHA256SUMS").read_text().splitlines():
    h,rel=line.split("  ",1); self.assertEqual(h,sha(p/rel))

if __name__=='__main__': unittest.main()
