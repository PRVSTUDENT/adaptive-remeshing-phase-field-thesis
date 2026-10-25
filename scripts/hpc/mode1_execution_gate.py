"""Technical execution checks and once-only accounting; no permission credentials.

The user removed per-job authorization on 2026-10-16. This module checks
qualified Mode-I manifests, resources, duplicates and scientific dependencies.
Historical controller permits and issuer pins are deliberately not consulted.
"""
import argparse
import base64
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
FROZEN_UEL = 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6'
EXPERIMENTAL_OFFSET_UEL = 'ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d'
EXPERIMENTAL_IRREVERSIBLE_UEL = 'e72e00d338e355b370fc5ebabfe6679f49bc07458d333b642b593c6710b16dad'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(command):
    return ' '.join(command.strip().split())


def load(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        try:return json.load(stream)
        except json.JSONDecodeError as error:raise ValueError('Malformed execution metadata: '+str(path)) from error


def validate_manifest(path, root=ROOT):
    path=Path(path).resolve()
    require(path.is_relative_to((root/'models/pandey_kumar_mode1').resolve()), 'Manifest outside Mode-I models')
    batch=load(path)
    require(batch.get('adapter') in ('mode1-qualified-batch-v2', 'mode1-experimental-offset-v1', 'mode1-continuum-preanalysis-v1', 'mode1-uel-trace-v1', 'mode1-pdas-iterative-v1', 'mode1-experimental-irrev-v1') and batch.get('scientific_scope')=='MODE1', 'Qualified Mode-I manifest required')
    require(batch.get('technical_stage') in ('C1-0','C1-1','C1-2','MODE1_BASELINE','EXPERIMENTAL_OFFSET','CONTINUUM_PREANALYSIS','UEL_TRACE','EXPERIMENTAL_IRREVERSIBLE'), 'Outside active scientific stages')
    require(batch.get('automatic_retry') is False, 'Blind automatic retries disallowed')
    jobs=batch['jobs']
    require(1 <= len(jobs)==batch['max_submissions'] <= 2, 'Batch must contain 1-2 named jobs')
    require(len({j['id'] for j in jobs})==len(jobs), 'Duplicate job IDs')
    run=batch.get('remote_run_dir','')
    require(re.fullmatch(r'/scratch9/pr21vyci/runs/mode1_[a-z0-9_/]+',run) and '..' not in run,'Unsafe scratch directory')
    files={}
    for name,expected in batch['files'].items():
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',name) and re.fullmatch(r'[0-9a-f]{64}',expected),'Unsafe filename/digest')
        actual=digest((path.parent/name).read_bytes())
        require(actual==expected,'Candidate hash mismatch: '+name)
        files[name]=actual
    is_experimental = (batch.get('adapter') == 'mode1-experimental-offset-v1' or batch.get('configuration') == 'EXPERIMENTAL_OFFSET')
    is_experimental_irrev = (batch.get('adapter') == 'mode1-experimental-irrev-v1' or batch.get('configuration') == 'STAGGERED_IRREVERSIBLE')
    is_continuum = (batch.get('adapter') == 'mode1-continuum-preanalysis-v1' or batch.get('configuration') == 'CONTINUUM_PREANALYSIS')
    is_trace = batch.get('adapter') == 'mode1-uel-trace-v1'
    if is_trace:
        require(batch.get('diagnostic_kind')=='NONINVASIVE_HISTORY_CALL_TRACE' and batch.get('hypothesis'), 'Reviewed trace hypothesis required')
        require(files.get('f42_experimental_offset_uel.for')==EXPERIMENTAL_OFFSET_UEL and files.get('job_notifications.sh'), 'Pinned trace parent/notifications required')
        sys.path.insert(0,str(ROOT/'scripts/validation'))
        from probe_mode1_f1597_uel_call_trace import instrument
        require((path.parent/'f42_history_trace_uel.for').read_bytes()==instrument((path.parent/'f42_experimental_offset_uel.for').read_bytes(),absolute_trace=batch.get('instrumentation_revision')==2), 'Only deterministic logging instrumentation is qualified')
        require(len(jobs)==1 and jobs[0].get('user_subroutine')=='f42_history_trace_uel.for' and jobs[0]['id']==('M1_F1597_HISTORY_TRACE_R2' if batch.get('instrumentation_revision')==2 else 'M1_F1597_HISTORY_TRACE_650'), 'Exact trace job/source required')
        require(files.get(jobs[0]['input'])=='58b1e69f40c5a65c7b9f1049e42ad745152ab8b5cf6b0f15547ed3276cd54964' and files.get('offset_state_table.csv')=='87c7954efef0134094bbfb03d7ada03d66f9a84281d0bb50f524ae88dfc65add', 'Authentic unchanged receiver state required')
        require('USER_SUB="f42_history_trace_uel.for"' in (path.parent/jobs[0]['pbs']).read_text(), 'PBS trace source differs')
    elif is_experimental:
        require(batch.get('hypothesis'), 'Scientific hypothesis required for experimental configuration')
        require(files.get('f42_experimental_offset_uel.for')==EXPERIMENTAL_OFFSET_UEL and files.get('job_notifications.sh'), 'Experimental offset UEL and notifications required')
    elif is_experimental_irrev:
        require(batch.get('hypothesis'), 'Scientific hypothesis required for experimental irreversible configuration')
        require(files.get('f42_experimental_irreversible_uel.for')==EXPERIMENTAL_IRREVERSIBLE_UEL and files.get('job_notifications.sh'), 'Experimental irreversible UEL and notifications required')
    elif is_continuum:
        require(batch.get('hypothesis'), 'Scientific hypothesis required for continuum pre-analysis configuration')
        require(files.get('job_notifications.sh'), 'Notifications required for continuum pre-analysis configuration')
    else:
        require(files.get('f42_mixed_uel.for')==FROZEN_UEL and files.get('job_notifications.sh'), 'Frozen UEL and notifications required')
    require(batch.get('acceptance'),'Scientific acceptance criteria required')
    seen=set()
    for job in jobs:
        require(job['cpus']==1 and type(job['memory_gb']) is int and 1<=job['memory_gb']<=16 and type(job['walltime_hours']) is int and 1<=job['walltime_hours']<=8,'Resource bounds exceeded')
        require(job['execution']=='single-rank serial' and job['queue']=='entry_imfdfkmq','Single-rank serial routing required')
        require(job['max_submissions']==1 and job.get('purpose') and job.get('input') in files,'Bound input/purpose/once-only limit required')
        require(re.fullmatch(r'submit_M1_[A-Z0-9_]+[.]pbs',job['pbs']) and job['pbs'] in files,'Unbound/unsafe PBS script')
        expected='powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq '+run+'/'+job['pbs']+'"'
        require(job['command']==expected and digest(canonical(expected).encode())==job['command_sha256'],'Command differs from exact guarded manifest')
        require(set(job.get('depends_on',[]))<=seen,'Unknown or cyclic predecessor')
        seen.add(job['id'])
    return batch,digest(path.read_bytes()),files


@contextlib.contextmanager
def locked(root=ROOT):
    # An OS lock outside coordination avoids committing a runtime lock artifact.
    lockpath=Path(tempfile.gettempdir())/('mode1-execution-'+digest(str(root.resolve()).encode())[:20]+'.lock')
    with lockpath.open('a+b') as stream:
        if os.name=='nt':
            import msvcrt
            if stream.tell()==0:stream.write(b'0');stream.flush()
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX)
        try:yield
        finally:
            if os.name=='nt':stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream,fcntl.LOCK_UN)


def ledger_path(root):
    return root/'project_coordination/MODE1_EXECUTION_LEDGER.json'


def read_ledger(root):
    return load(ledger_path(root)) if ledger_path(root).is_file() else {'version':1,'batches':{}}


def save_ledger(data,root):
    path=ledger_path(root);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+str(uuid.uuid4())+'.tmp.json')
    with temp.open('x',encoding='utf-8') as stream:
        json.dump(data,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    try:
        os.replace(temp,path)
    except (PermissionError, OSError):
        with path.open('w',encoding='utf-8') as stream:
            json.dump(data,stream,indent=2);stream.flush();os.fsync(stream.fileno())
        if temp.exists():
            try: temp.unlink()
            except OSError: pass


def receipts(root,key):
    path=root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json'
    return load(path).get(key,{}) if path.is_file() else {}


def prepare(request,root=ROOT):
    batch,key,files=validate_manifest(request['manifest_path'],root)
    proof=request['preflight']
    require(all(proof.get(k) is True for k in ('passed','pbs_email_verified','telegram_verified')),'Actual notification preflight failed')
    require(proof.get('candidate_manifest_sha256')==key and proof.get('file_hashes')==files,'Preflight is not bound to current manifest/files')
    require(proof.get('batch_spec_sha256')==digest(json.dumps(batch,sort_keys=True,separators=(',',':')).encode()),'Preflight batch mismatch')
    require(-30 <= (datetime.now(timezone.utc)-datetime.fromisoformat(proof['checked_at'])).total_seconds()<300,'Refresh technical preflight')
    require(type(proof.get('active_job_count')) is int and 0<=proof['active_job_count']<4,'Live scheduler resource count required')
    for job in batch['jobs']:
        dc=proof.get('datachecks',{}).get(job['id'],{})
        require(dc.get('status')=='PASS' and dc.get('input_sha256')==files[job['input']] and re.fullmatch(r'[0-9a-f]{64}',dc.get('dat_sha256','')),'Input-bound datacheck required')
        if batch.get('adapter')=='mode1-uel-trace-v1':
            require(dc.get('source_sha256')==files[job['user_subroutine']] and proof.get('trace_datacheck_binding')=='PASS','Source-bound trace datacheck required')
    with locked(root):
        data=read_ledger(root)
        record=data['batches'].setdefault(key,{'manifest_path':str(Path(request['manifest_path']).resolve()),'attempts':{},'audit':[]})
        for jobid,item in receipts(root,key).items():
            require(any(j['id']==jobid and j['command_sha256']==item.get('command_sha256') for j in batch['jobs']),'Receipt command mismatch')
            require(re.fullmatch(r'\d+[.]mmaster02',item.get('pbs_job_id','')),'Malformed actual PBS receipt')
            # Import existing accepted jobs; never rerun after removing permits.
            record['attempts'][jobid]=max(1,record['attempts'].get(jobid,0))
        record['preflight']=proof
        record['qualified_at']=datetime.now(timezone.utc).isoformat()
        save_ledger(data,root)
    return key


def dependency_error(batch,key,job,root=ROOT):
    if not job.get('depends_on'):return None
    try:
        path=(root/batch['dependency_review_path']).resolve()
        require(path.is_relative_to((root/'project_coordination').resolve()),'Review outside coordination')
        require(path.is_file(),'Predecessor scientific review pending')
        review=load(path)
        require(review.get('scientific_review')=='PASS','Predecessor scientific review has not passed')
        require(review.get('batch_manifest_sha256')==key and review.get('terminal_exit_status')==0 and review.get('reviewed_by') and review.get('evidence_report'),'Incomplete predecessor review')
        actual=receipts(root,key)
        for predecessor in job['depends_on']:
            require(actual.get(predecessor,{}).get('pbs_job_id')==review.get('predecessor_pbs_job_id') and re.fullmatch(r'\d+[.]mmaster02',review.get('predecessor_pbs_job_id','')),'Actual predecessor PBS receipt missing')
        require(batch.get('dependency_thresholds') and batch.get('required_state_checks'),'Scientific gates missing')
        for name,limit in batch['dependency_thresholds'].items():
            value=float(review['metrics'][name]);require(math.isfinite(value) and 0<=value<=limit,'Failed quantitative criterion: '+name)
        require(all(review.get('state_checks',{}).get(name) is True for name in batch['required_state_checks']),'State preservation unverified')
        hashes=review.get('evidence_hashes',{})
        require(hashes and all(re.fullmatch(r'[0-9a-fA-F]{64}',h) for h in hashes.values()),'Actual hashed evidence required')
    except (ValueError,KeyError,TypeError) as error:return str(error)
    return None


def reserve(command,root=ROOT):
    with locked(root):
        data=read_ledger(root)
        for key,record in data['batches'].items():
            path=Path(record['manifest_path'])
            if not path.is_file() or digest(path.read_bytes())!=key:continue  # Superseded frozen revision, audit retained.
            batch,livekey,_=validate_manifest(record['manifest_path'],root)
            matches=[j for j in batch['jobs'] if canonical(j['command'])==canonical(command)]
            if not matches:continue
            require(livekey==key,'Manifest changed; refresh technical preflight')
            require(len(matches)==1,'Ambiguous job command')
            job=matches[0]
            proof=record['preflight']
            checked=datetime.fromisoformat(proof['checked_at'])
            reservations=sum(1 for b in data['batches'].values() for event in b.get('audit',[]) if event.get('event')=='SUBMISSION_RESERVED' and datetime.fromisoformat(event['at'])>=checked)
            require(proof['active_job_count']+reservations<4,'Project resource slots occupied; refresh technical scheduler preflight')
            require(record['attempts'].get(job['id'],0)==0 and job['id'] not in receipts(root,key),'Job already submitted/reserved; reconcile scheduler; no duplicate')
            error=dependency_error(batch,key,job,root);require(error is None,error)
            record['attempts'][job['id']]=1
            record['audit'].append({'job':job['id'],'event':'SUBMISSION_RESERVED','at':datetime.now(timezone.utc).isoformat(),'command_sha256':job['command_sha256']})
            save_ledger(data,root);return
        raise ValueError('No matching technically qualified manifest; run Invoke-Mode1Execution.ps1')


def status(key,root=ROOT):
    data=read_ledger(root);record=data['batches'][key];batch,actual,_=validate_manifest(record['manifest_path'],root)
    require(actual==key,'Manifest changed; refresh preflight')
    ready=[];blocked=[]
    for job in batch['jobs']:
        if record['attempts'].get(job['id'],0) or job['id'] in receipts(root,key):continue
        error=dependency_error(batch,key,job,root)
        if error:blocked.append({'job':job['id'],'reason':error})
        else:ready.append(job['id'])
    return {'ready_jobs':ready,'blocked_jobs':blocked,'attempts':record['attempts']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--command64');parser.add_argument('--status')
    args=parser.parse_args()
    try:
        if args.prepare:
            incoming=sys.stdin.read().lstrip('\ufeff\xef\xbb\xbf')
            require(bool(incoming.strip()),'Empty technical preflight transport')
            try:
                if not incoming.lstrip().startswith('{'):incoming=base64.b64decode(incoming.strip(),validate=True).decode('utf-8')
                request=json.loads(incoming)
            except json.JSONDecodeError as error:raise ValueError('Invalid technical preflight JSON transport') from error
            print(json.dumps({'manifest_sha256':prepare(request)}))
        elif args.status:print(json.dumps(status(args.status)))
        elif args.command64:
            reserve(base64.b64decode(args.command64,validate=True).decode());print(json.dumps({'decision':'allow'}))
        else:raise ValueError('Missing technical execution action')
    except Exception as error:
        print(json.dumps({'decision':'deny','reason':str(error)}));return 1
    return 0

if __name__=='__main__':sys.exit(main())
