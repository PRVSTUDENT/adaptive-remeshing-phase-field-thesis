from __future__ import print_function
import hashlib,json,os,re,sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
PKG=os.path.join(ROOT,'models','generated','mode_ii','f21_native_remesh_execution')
def read(rel):
 with open(os.path.join(ROOT,rel),'rb') as h: return h.read().decode('utf-8')
def sha(path):
 d=hashlib.sha256(); d.update(open(path,'rb').read()); return d.hexdigest()
def validate():
 failures=[]
 required=['M2RMEXEC1.pbs','PACKAGE_MANIFEST.json','F21_RUNTIME_MANIFEST.json','F21_NO_EXECUTION_AUDIT.json','F21_MANIFEST_ALLOWLIST.json','STATUS.json','runtime/execute_f21_native_remesh.py','runtime/f21_abaqus_python_compatibility.py','runtime/collect_f21_evidence.py','runtime/job_notifications.sh','runtime/notification_evidence.py','runtime/source_deck.inp']
 for item in required:
  if not os.path.isfile(os.path.join(PKG,item)): failures.append('missing '+item)
 script=read('models/generated/mode_ii/f21_native_remesh_execution/runtime/execute_f21_native_remesh.py')
 if script.count('model.adaptiveRemesh(odb)')!=1: failures.append('native route must occur exactly once')
 for bad in ('AdaptivityProcess(','mdb.JobFromInputFile(','job.submit('):
  if bad in script: failures.append('prohibited marker '+bad)
 if "M2RMEXEC1_candidate.inp" not in script: failures.append('candidate name')
 pbs=read('models/generated/mode_ii/f21_native_remesh_execution/M2RMEXEC1.pbs')
 for token in ('F21_PACKAGE_DIR','F21_EVIDENCE_DIR','#PBS -l select=1:ncpus=1:mem=8gb','#PBS -l walltime=00:30:00','notify_start','notification_install_terminal_trap'):
  if token not in pbs: failures.append('pbs '+token)
 orch=read('scripts/hpc/stage_f/submit_stage_f21_native_remesh.sh')
 if orch.count('qsub -v')!=1 or 'qsub -V' in orch: failures.append('orchestrator qsub contract')
 if 'F21_PACKAGE_DIR=${package},F21_EVIDENCE_DIR=${evidence}' not in orch: failures.append('qsub variables')
 if sha(os.path.join(PKG,'runtime','source_deck.inp'))!='a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2': failures.append('source deck hash')
 for name in ('PACKAGE_MANIFEST.json','F21_RUNTIME_MANIFEST.json','F21_NO_EXECUTION_AUDIT.json','F21_MANIFEST_ALLOWLIST.json','STATUS.json'):
  json.load(open(os.path.join(PKG,name),'r'))
 return failures
if __name__=='__main__':
 f=validate(); print(json.dumps({'classification':'pass' if not f else 'fail','failures':f},sort_keys=True)); sys.exit(1 if f else 0)
