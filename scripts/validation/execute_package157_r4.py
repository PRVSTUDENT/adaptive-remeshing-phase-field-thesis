"""Registered exact R4 adapter; all submissions use the once-only controller."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

OPERATION='execute_mode1_package157_c1_2_r4_adaptive_continuation'
REL='models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r4/EXECUTION_MANIFEST.json'
JOB='M1_C4_P157_C1_2_R4'


def execute(root,output):
    root=Path(root).resolve(); output=Path(output).resolve()
    if not output.is_relative_to(root/'results/validation') or output.exists():
        raise ValueError('Fresh governed output path required')
    command=". './scripts/controller/Controller-Operations.ps1'; $op=Get-ControllerOperation -ArtifactId '"+OPERATION+"' -Workspace (Get-Location).Path; if(-not $op.executable){throw 'Unqualified R4'}"
    subprocess.run(['powershell','-NoProfile','-Command',"$ErrorActionPreference='Stop'; "+command],cwd=root,check=True,timeout=30,stdin=subprocess.DEVNULL)
    subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'scripts/hpc/Invoke-Mode1Execution.ps1'),'-ManifestPath',str(root/REL)],cwd=root,check=True,timeout=600,stdin=subprocess.DEVNULL)
    key=hashlib.sha256((root/REL).read_bytes()).hexdigest()
    receipts=json.loads((root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json').read_text(encoding='utf-8-sig'))
    receipt=receipts[key][JOB]
    batch=json.loads((root/REL).read_text())
    if not re.fullmatch(r'\d+\.mmaster02',receipt['pbs_job_id']) or receipt['command_sha256']!=batch['jobs'][0]['command_sha256']:
        raise ValueError('Unverified receipt; never retry')
    with (root/'project_coordination/HPC_JOB_LEDGER.csv').open(encoding='utf-8-sig',newline='') as stream:
        if not any(r['Job_ID']==receipt['pbs_job_id'] and r['Job_Name']==JOB for r in csv.DictReader(stream)):
            raise ValueError('Receipt missing once-only accounting')
    qrel='scripts/validation/'+OPERATION+'.qualification.json'
    q=json.loads((root/qrel).read_text())
    sources={p:hashlib.sha256((root/p).read_bytes()).hexdigest().upper()
             for p in list(q['scientific_dependencies'])+[qrel,'scripts/validation/execute_package157_r4.py']}
    payload=dict(schema=1,operation=OPERATION,verification_passed=True,
        status='SUBMITTED_AWAITING_PHYSICAL_VALIDATION',physical_acceptance='UNVERIFIED',
        pbs_job_id=receipt['pbs_job_id'],measurements={'submitted_jobs':1},sources=sources,
        finding='Reviewed R4 loading-subdivision experiment submitted exactly once; physical acceptance remains unverified.')
    with output.open('x') as stream:json.dump(payload,stream,indent=2)
    return payload


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workspace',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--operation-id',choices=[OPERATION],default=OPERATION)
    args=parser.parse_args();print(json.dumps(execute(args.workspace,args.output),indent=2))
