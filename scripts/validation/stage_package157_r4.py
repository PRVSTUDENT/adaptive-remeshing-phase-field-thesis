"""Guarded bounded uploads and actual cluster qualification; no qsub."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.state_transfer.build_package157_r4 import REL, REMOTE, SOURCES
PACKAGE=ROOT/REL
OUT=ROOT/'results/validation/package157_maintenance'


def guarded(*args):
    run=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(ROOT/'.agents/scripts/Invoke-GuardedSsh.ps1')]+list(args),cwd=str(ROOT),
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        universal_newlines=True,timeout=150)
    if run.returncode:
        raise RuntimeError(run.stderr+'\n'+run.stdout)
    return run.stdout


def remote(command):
    return guarded('-RemoteCommand',command,'-TimeoutSeconds','120')


def upload(path,target):
    return guarded('-UploadFile',str(path),'-RemotePath',target,'-TimeoutSeconds','120')


def stage():
    OUT.mkdir(exist_ok=True)
    remote('test ! -e '+REMOTE+' && mkdir -p '+REMOTE+'/runtime/scripts/state_transfer '+REMOTE+'/runtime/scripts/validation')
    batch=json.loads((PACKAGE/'EXECUTION_MANIFEST.json').read_text())
    for name in list(batch['files'])+['EXECUTION_MANIFEST.json','QUALIFICATION_EXECUTION_MANIFEST.json']:
        upload(PACKAGE/name,REMOTE+'/'+name)
    for name in SOURCES:
        upload(ROOT/name,REMOTE+'/runtime/'+name)
    for name in ['scripts/validation/verify_package157_staging.py','scripts/validation/package157_login_datachecks.sh']:
        upload(ROOT/name,REMOTE+'/runtime/'+name)
    print(remote('python3 '+REMOTE+'/runtime/scripts/validation/verify_package157_staging.py '+REMOTE),flush=True)
    result=remote('bash '+REMOTE+'/runtime/scripts/validation/package157_login_datachecks.sh')
    print(result,flush=True)
    proof=remote('python3 '+REMOTE+'/runtime/scripts/validation/verify_package157_staging.py '+REMOTE+' .')
    (OUT/'login_datachecks.json').write_text(proof)
    startup=remote('test -f '+REMOTE+'/login_startup.json && cat -- '+REMOTE+'/login_startup.json')
    (OUT/'login_startup.json').write_text(startup)
    print(proof,flush=True)


def compute_evidence():
    proof=remote('python3 '+REMOTE+'/runtime/scripts/validation/verify_package157_staging.py '+REMOTE+' compute_datacheck')
    startup=remote('test -f '+REMOTE+'/compute_startup.json && cat -- '+REMOTE+'/compute_startup.json')
    host=remote('test -f '+REMOTE+'/compute_datacheck_host.txt && cat -- '+REMOTE+'/compute_datacheck_host.txt').strip()
    (OUT/'compute_datachecks.json').write_text(proof)
    (OUT/'compute_startup.json').write_text(startup)
    (OUT/'compute_node.json').write_text(json.dumps(dict(host=host),indent=2)+'\n')
    print(proof,flush=True)


def refresh_preflight():
    remote('test ! -e '+REMOTE+'/compute_datacheck')
    for name in ['PACKAGE_MANIFEST.json','EXECUTION_MANIFEST.json','QUALIFICATION_EXECUTION_MANIFEST.json',
                 'submit_M1_C4_P157_C1_2_R4.pbs','submit_M1_C4_P157_R4_DC.pbs']:
        upload(PACKAGE/name,REMOTE+'/'+name)


if __name__=='__main__':
    if sys.argv[1:]==['--collect-compute']:
        compute_evidence()
    elif sys.argv[1:]==['--refresh-preflight']:
        refresh_preflight()
    else:
        stage()
