"""Exact Package73 preparation, staging, datacheck and parity evidence.

No qsub here. Actual submissions use Invoke-Mode1Execution.ps1 exclusively.
"""
import argparse
import base64
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from probe_mode1_f1597_uel_call_trace import instrument, PARENT_SHA, PACKAGE, PARENT

RUN = '/scratch9/pr21vyci/runs/mode1_package73_history_call_trace'
JOB = 'M1_F1597_HISTORY_TRACE_650'
BASE_RUN=RUN
BASE_JOB=JOB
REVISION=1


def digest(data): return hashlib.sha256(data).hexdigest()


def save(path, value):
    data = (json.dumps(value, indent=2)+'\n').encode() if not isinstance(value, bytes) else value
    if path.exists() and path.read_bytes() != data:
        raise ValueError('Preserve differing qualified candidate: '+str(path))
    if not path.exists(): path.write_bytes(data)


def prepare(root):
    folder = root/PACKAGE
    parent = (root/(PARENT+'f42_experimental_offset_uel.for')).read_bytes()
    candidate = folder/'f42_history_trace_uel.for'
    folder.mkdir(parents=True,exist_ok=True)
    if not candidate.exists():save(candidate,instrument(parent,absolute_trace=REVISION==2))
    if candidate.read_bytes() != instrument(parent,absolute_trace=REVISION==2): raise ValueError('Non-deterministic instrumentation')
    if REVISION==2:save(folder/'.gitattributes',b'f42_history_trace_uel.for -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n')
    for name in ('f42_experimental_offset_uel.for','offset_state_table.csv','job_notifications.sh'):
        save(folder/name, (root/(PARENT+name)).read_bytes())
    save(folder/(JOB+'.inp'), (root/(PARENT+'M1_EXP_COUPLED_TRANSFER_650.inp')).read_bytes())
    baseline = PARENT+'evidence_1415199/'
    plan = dict(schema=1, parent_pbs_job_id='1415199.mmaster02',
        purpose='Logging-only diagnostic; no corrected-transfer or retry claim',
        hypothesis='Actual JTYPE2 trial-history max updates alter what a later JTYPE1 call reads before LOP2 accepts the increment.',
        baseline_sources={p:digest((root/p).read_bytes()) for p in
            (baseline+'uel_energy_balance.csv', baseline+'M1_EXP_COUPLED_TRANSFER_650.dat')},
        force_samples='All N_RP U2/RF2 printed rows; require equal sample count and displacement sequence',
        energy_samples='All accepted-increment elastic/fracture/total rows; match step, increment and time',
        force_rtol=1e-8, force_atol_kN=1e-12, energy_rtol=1e-8, energy_atol_kNmm=1e-14,
        rationale='Unchanged input/offsets/equations, identical Abaqus2023 serial path; tolerance exceeds last printed decimal roundoff and does not excuse changed acceptance path.',
        reject_on='Nonfinite data, changed increments, truncation, wrong source/receipt or parity outside tolerances. No automatic resubmission.')
    save(folder/'PARITY_PLAN.json', plan)
    pbs = (root/(PARENT+'submit_M1_EXP_COUPLED_TRANSFER_650.pbs')).read_text()
    pbs = pbs.replace('M1_COUPLED_650','M1_HIST_TRACE').replace(
        '/scratch9/pr21vyci/runs/mode1_package72_coupled_state_transfer', RUN).replace(
        'M1_EXP_COUPLED_TRANSFER_650',JOB).replace('f42_experimental_offset_uel.for','f42_history_trace_uel.for')
    pbs = pbs.replace('Coupled Equilibrated State Transfer Solve','Non-invasive History Call Trace Diagnostic')
    if REVISION==2:
        hook="""# Record only transport return codes and event names; never tokens or API bodies.
unset NOTIFICATION_MOCK_TELEGRAM NOTIFICATION_MOCK_FAIL
_definition="$(declare -f notification_send_telegram_once)"
eval "${_definition/notification_send_telegram_once/trace_original_telegram_once}"
_definition="$(declare -f notification_send_email_once)"
eval "${_definition/notification_send_email_once/trace_original_email_once}"
notification_send_telegram_once() {
 local event=UNKNOWN rc=0
 case "$1" in *STARTED*) event=STARTED;; *COMPLETED*) event=COMPLETED;; *FAILED*) event=FAILED;; *TERMINATED*) event=TERMINATED;; esac
 trace_original_telegram_once "$@" || rc=$?
 printf '%s TELEGRAM %s %s\\n' "$PBS_JOBID" "$event" "$rc" >> "$RUN_DIR/notification_delivery.tsv"
 return "$rc"
}
notification_send_email_once() {
 local event=UNKNOWN rc=0
 case "$2" in *STARTED*) event=STARTED;; *COMPLETED*) event=COMPLETED;; *FAILED*) event=FAILED;; *TERMINATED*) event=TERMINATED;; esac
 if command -v sendmail >/dev/null 2>&1; then trace_original_email_once "$@" || rc=$?; else rc=127; fi
 printf '%s EMAIL %s %s\\n' "$PBS_JOBID" "$event" "$rc" >> "$RUN_DIR/notification_delivery.tsv"
 return "$rc"
}
"""
        save(folder/'trace_notification_receipts.sh',hook.encode())
        pbs=pbs.replace('notification_load_config\n','notification_load_config\nsource "${RUN_DIR}/trace_notification_receipts.sh"\n',1)
    save(folder/('submit_'+JOB+'.pbs'), pbs.replace('\r\n','\n').encode())
    names=['f42_experimental_offset_uel.for','f42_history_trace_uel.for','offset_state_table.csv',
           'job_notifications.sh',JOB+'.inp','submit_'+JOB+'.pbs','PARITY_PLAN.json']
    if REVISION==2:names.append('trace_notification_receipts.sh')
    hashes={n:digest((folder/n).read_bytes()) for n in names}
    save(folder/'PACKAGE_MANIFEST.json',dict(package_number=73, purpose=plan['purpose'], files=hashes))
    hashes['PACKAGE_MANIFEST.json']=digest((folder/'PACKAGE_MANIFEST.json').read_bytes())
    command='powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq '+RUN+'/submit_'+JOB+'.pbs"'
    batch=dict(batch_name='MODE1_'+JOB[3:], adapter='mode1-uel-trace-v1',
        technical_stage='UEL_TRACE', configuration='NONINVASIVE_HISTORY_TRACE', scientific_scope='MODE1',
        hypothesis=plan['hypothesis'], max_submissions=1, automatic_retry=False, remote_run_dir=RUN,
        diagnostic_kind='NONINVASIVE_HISTORY_CALL_TRACE', files=hashes,
        jobs=[dict(id=JOB,pbs='submit_'+JOB+'.pbs',command=command,command_sha256=digest(' '.join(command.split()).encode()),
            max_submissions=1,depends_on=[],purpose=plan['purpose'],cpus=1,memory_gb=16,walltime_hours=4,
            queue='entry_imfdfkmq',execution='single-rank serial',input=JOB+'.inp',
            user_subroutine='f42_history_trace_uel.for',datacheck=JOB+'_DC.dat')],
        acceptance={JOB:'Abaqus2023 Exit0; bounded paired UEL/lifecycle trace; unchanged accepted increments; all RF/energy samples pass predeclared parity. Transfer remains failed.'})
    if REVISION==2:batch['instrumentation_revision']=2
    save(folder/'TRACE_BATCH.json', batch)
    return batch


def remote(root, code, payload=None):
    # Only the canonical guarded SSH wrapper. Fixed target, bounded process and no stdin consumers.
    code=code.replace(BASE_RUN,RUN).replace(BASE_JOB,JOB)
    encoded=base64.b64encode(code.encode()).decode()
    args='' if payload is None else ' '+base64.b64encode(json.dumps(payload).encode()).decode()
    command="python3 -c 'import base64,sys;exec(base64.b64decode(sys.argv.pop(1)))' "+encoded+args
    result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'.agents/scripts/Invoke-GuardedSsh.ps1'),
        '-RemoteCommand',command], capture_output=True, text=True, timeout=125)
    if result.returncode: raise RuntimeError('Guarded SSH failed: '+result.stdout[-3000:]+result.stderr[-1000:])
    return result.stdout.strip()


def stage(root):
    batch=prepare(root); folder=root/PACKAGE
    names=list(batch['files'])+['TRACE_BATCH.json']
    payload={n:base64.b64encode((folder/n).read_bytes()).decode() for n in names}
    import gzip
    archive=gzip.compress(json.dumps(payload).encode(),mtime=0)
    archive_sha=digest(archive)
    code="""import base64,gzip,hashlib,json,pathlib,sys
+run=pathlib.Path('/scratch9/pr21vyci/runs/mode1_package73_history_call_trace')
+run.mkdir(parents=True,exist_ok=True)
+p=json.loads(base64.b64decode(sys.argv[1])); chunk=base64.b64decode(p['data'])
+if len(p['sha'])!=64 or any(c not in '0123456789abcdef' for c in p['sha']): raise RuntimeError('Invalid upload digest')
+upload=run/('.stage-'+p['sha']+'.bin'); offset=p['offset']
+old=upload.read_bytes() if upload.exists() else b''
+if len(old)==offset: upload.write_bytes(old+chunk)
+elif old[offset:offset+len(chunk)]!=chunk: raise RuntimeError('Conflicting upload; preserve')
+if p['last']:
+ data=upload.read_bytes()
+ if hashlib.sha256(data).hexdigest()!=p['sha']: raise RuntimeError('Upload digest mismatch')
+ for name,value in json.loads(gzip.decompress(data)).items():
+  if pathlib.Path(name).name!=name: raise RuntimeError('Unsafe file')
+  path=run/name; value=base64.b64decode(value)
+  if path.exists() and path.read_bytes()!=value: raise RuntimeError('Preserve differing staged file: '+name)
+  if not path.exists(): path.write_bytes(value)
+ print('STAGED_EXACT_PACKAGE73_FILES')
+else: print('UPLOAD_CHUNK_VERIFIED')
+""".replace('\n+','\n')
    for offset in range(0,len(archive),9000):
        output=remote(root,code,dict(sha=archive_sha,offset=offset,data=base64.b64encode(archive[offset:offset+9000]).decode(),last=offset+9000>=len(archive)))
    return output



def datacheck(root):
    code="""import hashlib,json,pathlib,subprocess
run=pathlib.Path('/scratch9/pr21vyci/runs/mode1_package73_history_call_trace')
dc=run/'datacheck_v1'; dc.mkdir(exist_ok=True)
name='M1_F1597_HISTORY_TRACE_650_DC'
for filename in ('M1_F1597_HISTORY_TRACE_650.inp','f42_history_trace_uel.for','offset_state_table.csv'):
 target=dc/filename; data=(run/filename).read_bytes()
 if target.exists() and target.read_bytes()!=data: raise RuntimeError('Preserve datacheck revision')
 if not target.exists(): target.write_bytes(data)
proof=run/'DATACHECK_BINDING.json'
if proof.exists(): print(proof.read_text()); raise SystemExit(0)
if (dc/(name+'.dat')).exists() and (dc/'qualification_console.txt').exists():
 dat=(dc/(name+'.dat')).read_bytes(); log=(dc/'qualification_console.txt').read_bytes()
 if b'ANALYSIS DATACHECK COMPLETE' not in dat or b'***ERROR' in dat or b'End Linking Abaqus/Standard User Subroutines' not in log or ('Abaqus JOB '+name+' COMPLETED').encode() not in log: raise RuntimeError('Incomplete prior datacheck; preserve, no retry')
 (run/(name+'.dat')).write_bytes(dat)
 files={n:hashlib.sha256((dc/n).read_bytes()).hexdigest() for n in ('M1_F1597_HISTORY_TRACE_650.inp','f42_history_trace_uel.for','offset_state_table.csv')}
 record=dict(status='PASS',solver='Abaqus/Standard 2023',exit_code=0,files=files,dat_sha256=hashlib.sha256(dat).hexdigest(),log_sha256=hashlib.sha256(log).hexdigest(),log_kind='CAPTURED_INTERACTIVE_CONSOLE',datacheck_directory=str(dc))
 proof.write_text(json.dumps(record,indent=2)+'\\n'); print(json.dumps(record)); raise SystemExit(0)
if (dc/(name+'.log')).exists() or (dc/'qualification_console.txt').exists(): raise RuntimeError('Datacheck already attempted; inspect evidence, no blind retry')
script=dc/'run_datacheck.sh'
script.write_text('''#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
cd /scratch9/pr21vyci/runs/mode1_package73_history_call_trace/datacheck_v1
timeout 100s abaqus job=M1_F1597_HISTORY_TRACE_650_DC input=M1_F1597_HISTORY_TRACE_650.inp user=f42_history_trace_uel.for cpus=1 datacheck interactive
''')
r=subprocess.run(['bash',str(script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,timeout=110)
(dc/'qualification_console.txt').write_text(r.stdout)
if r.returncode: print(r.stdout[-6000:]); raise RuntimeError('Datacheck failed; evidence preserved')
dat=(dc/(name+'.dat')).read_bytes(); log=(dc/'qualification_console.txt').read_bytes()
if b'ANALYSIS DATACHECK COMPLETE' not in dat or b'***ERROR' in dat: raise RuntimeError('Datacheck result failed')
(run/(name+'.dat')).write_bytes(dat)
files={n:hashlib.sha256((dc/n).read_bytes()).hexdigest() for n in ('M1_F1597_HISTORY_TRACE_650.inp','f42_history_trace_uel.for','offset_state_table.csv')}
record=dict(status='PASS',solver='Abaqus/Standard 2023',exit_code=0,files=files,dat_sha256=hashlib.sha256(dat).hexdigest(),log_sha256=hashlib.sha256(log).hexdigest(),datacheck_directory=str(dc))
proof.write_text(json.dumps(record,indent=2)+'\\n'); print(json.dumps(record))
"""
    return remote(root,code)


def forces(path):
    result=[]
    for line in path.read_text(errors='strict').splitlines():
        fields=line.split()
        if len(fields)==3 and fields[0]=='999999':
            try: result.append(tuple(float(x.replace('D','E')) for x in fields[1:]))
            except ValueError: pass
    if not result: raise ValueError('Missing N_RP force table')
    return result


def compare_parity(root, folder, package=None):
    package=package or PACKAGE
    plan=json.loads((root/package/'PARITY_PLAN.json').read_text())
    base=root/(PARENT+'evidence_1415199/')
    for path, expected in plan['baseline_sources'].items():
        if digest((root/path).read_bytes())!=expected: raise ValueError('Frozen baseline changed')
    reference=forces(base/'M1_EXP_COUPLED_TRANSFER_650.dat'); actual=forces(folder/'solver.dat')
    if len(reference)!=len(actual): raise ValueError('Changed force sample count')
    def compare(a,b,atol,rtol):
        if not (math.isfinite(a) and math.isfinite(b)): raise ValueError('Nonfinite parity value')
        if abs(a-b)>atol+rtol*abs(a): raise ValueError('Instrumentation numerical parity failed')
        return abs(a-b)/max(abs(a),atol)
    force_error=0.
    for (u,f),(u2,f2) in zip(reference,actual):
        compare(u,u2,1e-14,1e-10);force_error=max(force_error,compare(f,f2,plan['force_atol_kN'],plan['force_rtol']))
    def energy(path):
        with path.open() as f:return [[float(x) for x in row] for row in list(csv.reader(f))[1:] if row]
    ref=energy(base/'uel_energy_balance.csv');act=energy(folder/'uel_energy_balance.csv')
    if not ref or len(ref)!=len(act): raise ValueError('Changed accepted increments')
    error=0.
    for a,b in zip(ref,act):
        if len(a)!=7 or len(b)!=7 or a[:2]!=b[:2]: raise ValueError('Changed step/increment')
        for x,y in zip(a[2:4],b[2:4]):compare(x,y,1e-12,1e-10)
        for x,y in zip(a[4:],b[4:]):error=max(error,compare(x,y,plan['energy_atol_kNmm'],plan['energy_rtol']))
    return dict(status='PASS',force_relative_error=force_error,energy_relative_error=error,
        force_samples=len(actual),accepted_increments=len(act),baseline_sources=plan['baseline_sources'],
        sources={str(p.relative_to(root)).replace('\\','/'):digest(p.read_bytes()) for p in
            (folder/'solver.dat',folder/'uel_energy_balance.csv',root/package/'PARITY_PLAN.json')})


def collect(root, job_id):
    if not re.fullmatch(r'\d+\.mmaster02',job_id): raise ValueError('Exact PBS ID required')
    # Narrow explicit filenames only; never walk scratch trees or transfer solver binaries.
    code="""import base64,json,pathlib
run=pathlib.Path('/scratch9/pr21vyci/runs/mode1_package73_history_call_trace')
names={'solver.dat':'M1_F1597_HISTORY_TRACE_650.dat','solver.sta':'M1_F1597_HISTORY_TRACE_650.sta','solver.log':'pbs_execution.log','uel_energy_balance.csv':'uel_energy_balance.csv','f1597_uel_call_trace.csv':'f1597_uel_call_trace.csv','pbs_execution.log':'pbs_execution.log','DATACHECK_BINDING.json':'DATACHECK_BINDING.json','datacheck.dat':'M1_F1597_HISTORY_TRACE_650_DC.dat'}
if (run/'notification_delivery.tsv').is_file(): names['notification_delivery.tsv']='notification_delivery.tsv'
for name in names.values():
 if not (run/name).is_file(): raise RuntimeError('Expected artifact not yet available: '+name)
print(json.dumps({n:base64.b64encode((run/f).read_bytes()).decode() for n,f in names.items()}))
"""
    files=json.loads(remote(root,code));folder=root/PACKAGE/'evidence';folder.mkdir(exist_ok=True)
    for name,data in files.items():save(folder/name,base64.b64decode(data))
    if 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in (folder/'solver.sta').read_text(): raise ValueError('Solver did not complete')
    parity=compare_parity(root,folder);save(folder/'parity.json',parity)
    save(folder/'provenance.json',dict(pbs_job_id=job_id,job_name=JOB,solver='Abaqus/Standard 2023',exit_code=0,
        instrumented_source_sha256=digest((root/PACKAGE/'f42_history_trace_uel.for').read_bytes()),
        batch_manifest_sha256=digest((root/PACKAGE/'TRACE_BATCH.json').read_bytes()),
        evidence_files={n:digest((folder/n).read_bytes()) for n in list(files)+['parity.json']}))
    return parity


def finalize(root, job_id):
    if REVISION!=2: raise ValueError('Only the separately qualified absolute-output revision may become ready')
    folder=root/PACKAGE; evidence=folder/'evidence'
    batch=prepare(root); manifest_sha=digest((folder/'TRACE_BATCH.json').read_bytes())
    preflight=json.loads((folder/'NOTIFICATION_PREFLIGHT.json').read_text())
    if preflight.get('passed') is not True or preflight.get('trace_datacheck_binding')!='PASS' or preflight.get('telegram_verified') is not True or preflight.get('pbs_email_verified') is not True or preflight.get('candidate_manifest_sha256')!=manifest_sha or preflight['file_hashes']!=batch['files']:
        raise ValueError('Exact real preflight proof missing')
    for name,expected in batch['files'].items():
        if digest((folder/name).read_bytes())!=expected: raise ValueError('Qualified file changed')
    receipts=json.loads((root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json').read_text(encoding='utf-8-sig'))
    if receipts[manifest_sha][JOB]['pbs_job_id']!=job_id: raise ValueError('Actual guarded PBS receipt missing')
    code="""import base64,json,re,subprocess,sys
job=json.loads(base64.b64decode(sys.argv[1]))
if not re.fullmatch(r'\d+\.mmaster02',job): raise RuntimeError('Invalid exact job ID')
r=subprocess.run(['qstat','-fx',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
if r.returncode: raise RuntimeError('Cannot independently verify scheduler termination')
fields={}
for name in ('job_state','Exit_status','resources_used.walltime','obittime'):
 m=re.search(r'^\\s*'+re.escape(name)+r'\\s*=\\s*(.+)$',r.stdout,re.M)
 if not m: raise RuntimeError('Missing terminal field')
 fields[name]=m.group(1).strip()
fields['pbs_job_id']=job
print(json.dumps(fields))
"""
    terminal=json.loads(remote(root,code,job_id))
    if terminal['job_state']!='F' or terminal['Exit_status']!='0': raise ValueError('Diagnostic has not terminated successfully')
    save(evidence/'TERMINAL_STATUS.json',terminal)
    with (evidence/'notification_delivery.tsv').open() as handle:
        notifications=[line.split() for line in handle if line.strip()]
    required={(job_id,channel,event,'0') for channel in ('TELEGRAM','EMAIL') for event in ('STARTED','COMPLETED')}
    if set(map(tuple,notifications))!=required or len(notifications)!=4: raise ValueError('Actual compute start/terminal transport acknowledgements missing')
    save(evidence/'NOTIFICATION_VERIFICATION.json',dict(pbs_job_id=job_id,status='PASS',
        telegram='HTTP200_AND_OK_TRUE',email='SENDMAIL_ACCEPTED',started='PASS',completed='PASS',terminal_events=1,
        evidence_sha256=digest((evidence/'notification_delivery.tsv').read_bytes())))
    parity=compare_parity(root,evidence)
    if json.loads((evidence/'parity.json').read_text())!=parity: raise ValueError('Parity proof changed')
    with (evidence/'f1597_uel_call_trace.csv').open() as handle:rows=list(csv.reader(handle))
    from probe_mode1_f1597_uel_call_trace import HEADER
    if not 1<=len(rows)<=2048: raise ValueError('Empty or truncated trace')
    for index,row in enumerate(rows,1):
        if len(row)!=len(HEADER) or int(row[0])!=index or not all(math.isfinite(float(v)) for v in row): raise ValueError('Trace structural qualification failed')
    task=json.loads((root/'project_coordination/ACTIVE_TASK.json').read_text(encoding='utf-8-sig'))
    basis=task['scientific_checkpoint']
    if basis['operation']!='mapped_mechanical_history_call_order_probe' or digest((root/basis['artifact']).read_bytes()).upper()!=basis['sha256'].upper(): raise ValueError('Completed mechanical/history basis changed')
    files=[folder/n for n in list(batch['files'])+['TRACE_BATCH.json','NOTIFICATION_PREFLIGHT.json']]
    files += [p for p in evidence.iterdir() if p.is_file()]
    files += [root/basis['artifact'],root/'scripts/validation/probe_mode1_f1597_uel_call_trace.py',
              root/'scripts/validation/qualify_mode1_f1597_trace.py',
              root/'models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for']
    files += [root/p for p in parity['baseline_sources']]
    sources={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in files}
    # Bind the authentic original receiver files as well, not copies alone.
    sources.update({PARENT+n:digest((root/(PARENT+n)).read_bytes()) for n in
        ('f42_experimental_offset_uel.for','M1_EXP_COUPLED_TRANSFER_650.inp','offset_state_table.csv')})
    proof=dict(schema=1,operation='authentic_uel_history_call_trace',status='READY_FOR_TRACE_ANALYSIS',dispatch_ready=True,
        pbs_job_id=job_id,manifest_sha256=manifest_sha,datacheck='PASS',login_notifications='PASS',compute_notifications='PASS',
        parity='PASS',basis_artifact=basis['artifact'],basis_sha256=basis['sha256'],sources=sources,
        note='Ready for bounded scientific analysis of the separately acquired authentic trace. No previous scientific operation is reactivated.')
    save(folder/'QUALIFICATION.json',proof)
    return dict(status=proof['status'],dispatch_ready=True,pbs_job_id=job_id,trace_records=len(rows),
        force_relative_error=parity['force_relative_error'],energy_relative_error=parity['energy_relative_error'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--action',choices=['prepare','stage','datacheck','collect','finalize'],required=True);p.add_argument('--job-id')
    p.add_argument('--revision',type=int,choices=[1,2],default=1)
    a=p.parse_args();root=a.workspace.resolve()
    if a.revision==2:
        REVISION=2
        PACKAGE='models/pandey_kumar_mode1/74_method_c_history_call_trace_absolute_path/'
        RUN='/scratch9/pr21vyci/runs/mode1_package74_history_call_trace'
        JOB='M1_F1597_HISTORY_TRACE_R2'
    result=prepare(root) if a.action=='prepare' else stage(root) if a.action=='stage' else datacheck(root) if a.action=='datacheck' else collect(root,a.job_id) if a.action=='collect' else finalize(root,a.job_id)
    print(result if isinstance(result,str) else json.dumps(result))
