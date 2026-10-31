"""Controller-compatible pre-submission adapter; no direct scheduler commands.

Qualification means eligible for guarded technical checks, never physical PASS.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

OPERATION = 'evaluate_mode1_package148_state_transfer'
MANIFEST = 'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r1/EXECUTION_MANIFEST.json'


def operation_contract(operation_id):
    if operation_id == OPERATION:
        return MANIFEST, 'M1_C4_P148_R1', 'scripts/validation/execute_package148_state_transfer.qualification.json'
    if operation_id == OPERATION+'_r2':
        return (MANIFEST.replace('_r1/','_r2/'), 'M1_C4_P148_R2',
                'scripts/validation/evaluate_mode1_package148_state_transfer_r2.qualification.json')
    if operation_id == OPERATION+'_r3':
        return (MANIFEST.replace('_r1/','_r3/'), 'M1_C4_P148_R3',
                'scripts/validation/evaluate_mode1_package148_state_transfer_r3.qualification.json')
    if operation_id == OPERATION+'_r4':
        return (MANIFEST.replace('_r1/','_r4/'), 'M1_C4_P148_R4',
                'scripts/validation/evaluate_mode1_package148_state_transfer_r4.qualification.json')
    if operation_id == OPERATION+'_r5':
        return (MANIFEST.replace('_r1/','_r5/'), 'M1_C4_P148_R5',
                'scripts/validation/evaluate_mode1_package148_state_transfer_r5.qualification.json')
    if operation_id == OPERATION+'_r6':
        return (MANIFEST.replace('_r1/','_r6/'), 'M1_C4_P148_R6',
                'scripts/validation/evaluate_mode1_package148_state_transfer_r6.qualification.json')
    if operation_id == OPERATION+'_r7':
        return (MANIFEST.replace('_r1/','_r7/'), 'M1_C4_P148_R7',
                'scripts/validation/evaluate_mode1_package148_state_transfer_r7.qualification.json')
    if operation_id == OPERATION+'_r8':
        return (MANIFEST.replace('_r1/','_r8/'), 'M1_C4_P148_R8',
                'scripts/validation/evaluate_mode1_package148_state_transfer_r8.qualification.json')
    raise ValueError('Unregistered Package148 revision')


def verified_receipt(root, operation_id=OPERATION):
    relative, job_name, _ = operation_contract(operation_id)
    manifest = root / relative
    batch = json.loads(manifest.read_text(encoding='utf-8-sig'))
    key = hashlib.sha256(manifest.read_bytes()).hexdigest()
    receipts = json.loads((root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json').read_text(encoding='utf-8-sig'))
    receipt = receipts.get(key, {}).get(job_name, {})
    job_id = receipt.get('pbs_job_id', '')
    if not re.fullmatch(r'\d+\.mmaster02', job_id) or receipt.get('command_sha256') != batch['jobs'][0]['command_sha256']:
        raise ValueError('No matching authentic once-only submission receipt; reconcile, never retry blindly')
    import csv
    with (root/'project_coordination/HPC_JOB_LEDGER.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if not any(r.get('Job_ID') == job_id and r.get('Job_Name') == job_name for r in rows):
        raise ValueError('Accepted submission missing HPC job ledger accounting')
    return job_id


def execute(root, output, runner=subprocess.run, operation_id=OPERATION):
    manifest_relative, job_name, qualification_relative = operation_contract(operation_id)
    root = Path(root).resolve()
    output = Path(output).resolve()
    if not output.is_relative_to(root/'results/validation') or output.exists():
        raise ValueError('Fresh result path inside results/validation required')
    # Revalidate qualification immediately before invoking the technical gate.
    check = ". './scripts/controller/Controller-Operations.ps1'; $op=Get-ControllerOperation -ArtifactId '"+operation_id+"' -Workspace (Get-Location).Path; if($op.qualification.execution_mode -ne 'HPC_PRE_SUBMISSION'){throw 'Wrong execution mode'}"
    runner(['powershell','-NoProfile','-Command',"$ErrorActionPreference='Stop'; "+check], cwd=root, stdin=subprocess.DEVNULL, check=True, timeout=30)
    runner(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'scripts/hpc/Invoke-Mode1Execution.ps1'),'-ManifestPath',str(root/manifest_relative)], cwd=root, stdin=subprocess.DEVNULL, check=True, timeout=600)
    job_id = verified_receipt(root, operation_id)
    sources = {manifest_relative: hashlib.sha256((root/manifest_relative).read_bytes()).hexdigest().upper()}
    qualification = root/qualification_relative
    q = json.loads(qualification.read_text(encoding='utf-8-sig'))
    for name in [__file__, *q['scientific_dependencies'], str(qualification)]:
        path = Path(name) if Path(name).is_absolute() else root/name
        sources[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    payload = dict(schema=1, task_id='F1597', operation=operation_id, verification_passed=True,
                   status='SUBMITTED_AWAITING_PHYSICAL_VALIDATION', physical_acceptance='UNVERIFIED',
                   pbs_job_id=job_id, measurements={'submitted_jobs':1}, sources=sources,
                   finding='Authentic once-only '+job_name+' submission recorded as '+job_id,
                   limitation='Submission proves neither convergence nor physical acceptance.',
                   next_operation='Collect authentic '+job_name+' coupled results and independently evaluate predeclared physical gates.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2)
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--operation-id', default=OPERATION, choices=[OPERATION, OPERATION+'_r2', OPERATION+'_r3', OPERATION+'_r4', OPERATION+'_r5', OPERATION+'_r6', OPERATION+'_r7', OPERATION+'_r8'])
    args = parser.parse_args()
    print(json.dumps(execute(args.workspace, args.output, operation_id=args.operation_id)))
