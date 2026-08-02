import hashlib,json,pathlib,re

ROOT=pathlib.Path(__file__).resolve().parents[2]
CTL=ROOT/'models/generated/mode_ii/f18_penalty_active_rollback_control'
FRC=ROOT/'models/generated/mode_ii/f18_penalty_active_rollback_forced'
REG=ROOT/'models/generated/mode_ii/f18_native_adaptive_region_repair'

def test_rollback_identity_and_trigger():
 assert (CTL/'runtime/M2IRR_F18.for').read_bytes()==(FRC/'runtime/M2IRR_F18.for').read_bytes()
 assert (CTL/'runtime/M2IRR_F18.inp').read_bytes()==(FRC/'runtime/M2IRR_F18.inp').read_bytes()
 s=(CTL/'runtime/M2IRR_F18.for').read_text()
 for x in ('KSTEP.EQ.2','KINC.EQ.4','JELEM.EQ.6','INPT.EQ.1','PENRES.NE.ZERO','PENEDEN.GT.ZERO','PNEWDT=HALF','LATCH OUTSIDE SVARS'): assert x in s
 assert 'F18_FORCE_CUTBACK=0' in (CTL/'M2IRRROLLCTL4.pbs').read_text()
 assert 'F18_FORCE_CUTBACK=1' in (FRC/'M2IRRROLLFORCE4.pbs').read_text()

def test_adaptive_contract_and_lifetime():
 p=(REG/'M2RMREG5.pbs').read_text(); s=(REG/'runtime/qualify_f18_adaptive_region.py').read_text()
 assert 'export F18_SOURCE_ODB=' in p and 'sha256sum "$F18_SOURCE_ODB"' in p
 assert s.count('openOdb(')==1 and s.count('odb.close()')==1
 assert s.index('for value in values:') < s.index('odb.close()')
 for x in ("'MISESERI' not in fields",'if not values','physical=sum','assert all'): assert x in s

def test_manifests_and_final_lf():
 for d in (CTL,FRC,REG):
  assert (d/'F18_SHA256SUMS').read_bytes()==(d/'SHA256SUMS').read_bytes()
  for f in d.rglob('*'):
   if f.is_file(): assert f.read_bytes().endswith(b'\n')
  for line in (d/'F18_SHA256SUMS').read_text().splitlines():
   h,rel=line.split('  ',1); assert hashlib.sha256((d/rel).read_bytes()).hexdigest()==h

def test_orchestrator_bounds():
 s=(ROOT/'scripts/hpc/stage_f/submit_stage_f18_three_job_batch.sh').read_text()
 assert s.count('qsub ') == 3 and 'afterany:"$ctl"' in s
 assert 'qdel' not in s and 'qmove' not in s and 'retry' not in s.lower()
