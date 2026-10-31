# -*- coding: utf-8 -*-
"""
execute_package150_continuation.py
Mode-I Method C: Pre-submission execution adapter for Stage C1-2 forward continuation.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

OPERATION = 'evaluate_mode1_package150_stage_c1_2_continuation'
MANIFEST = 'models/pandey_kumar_mode1/150_c4_package150_c1_2_continuation/EXECUTION_MANIFEST.json'
QUALIFICATION = 'scripts/validation/evaluate_mode1_package150_stage_c1_2_continuation.qualification.json'
JOB_NAME = 'M1_C4_P150_C1_2'


def operation_contract(operation_id):
    if operation_id == OPERATION:
        return MANIFEST, JOB_NAME, QUALIFICATION
    raise ValueError('Unregistered Package150 operation: %s' % operation_id)


def verified_receipt(root, operation_id=OPERATION):
    relative, job_name, _ = operation_contract(operation_id)
    manifest = root / relative
    batch = json.loads(manifest.read_text(encoding='utf-8-sig'))
    key = hashlib.sha256(manifest.read_bytes()).hexdigest()
    receipts = json.loads((root / 'project_coordination/MODE1_BATCH_SUBMISSIONS.json').read_text(encoding='utf-8-sig'))
    receipt = receipts.get(key, {}).get(job_name, {})
    job_id = receipt.get('pbs_job_id', '')
    if not re.fullmatch(r'\d+\.mmaster02', job_id) or receipt.get('command_sha256') != batch['jobs'][0]['command_sha256']:
        raise ValueError('No matching authentic once-only submission receipt; reconcile, never retry blindly')
    import csv
    with (root / 'project_coordination/HPC_JOB_LEDGER.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if not any(r.get('Job_ID') == job_id and r.get('Job_Name') == job_name for r in rows):
        raise ValueError('Accepted submission missing HPC job ledger accounting')
    return job_id


def execute(root, output, runner=subprocess.run, operation_id=OPERATION):
    manifest_relative, job_name, qualification_relative = operation_contract(operation_id)
    root = Path(root).resolve()
    output = Path(output).resolve()
    if not output.is_relative_to(root / 'results/validation') or output.exists():
        raise ValueError('Fresh result path inside results/validation required')

    check = ". './scripts/controller/Controller-Operations.ps1'; $op=Get-ControllerOperation -ArtifactId '" + operation_id + "' -Workspace (Get-Location).Path; if($op.qualification.execution_mode -ne 'HPC_PRE_SUBMISSION'){throw 'Wrong execution mode'}"
    runner(['powershell', '-NoProfile', '-Command', "$ErrorActionPreference='Stop'; " + check], cwd=root, stdin=subprocess.DEVNULL, check=True, timeout=30)
    runner(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(root / 'scripts/hpc/Invoke-Mode1Execution.ps1'), '-ManifestPath', str(root / manifest_relative)], cwd=root, stdin=subprocess.DEVNULL, check=True, timeout=600)
    job_id = verified_receipt(root, operation_id)
    sources = {manifest_relative: hashlib.sha256((root / manifest_relative).read_bytes()).hexdigest().upper()}
    qualification = root / qualification_relative
    q = json.loads(qualification.read_text(encoding='utf-8-sig'))
    for name in [__file__, *q['scientific_dependencies'], str(qualification)]:
        path = Path(name) if Path(name).is_absolute() else root / name
        sources[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    payload = dict(
        schema=1, task_id='F1597', operation=operation_id, verification_passed=True,
        status='SUBMITTED_AWAITING_PHYSICAL_VALIDATION', physical_acceptance='UNVERIFIED',
        pbs_job_id=job_id, measurements={'submitted_jobs': 1}, sources=sources,
        finding='Authentic once-only ' + job_name + ' submission recorded as ' + job_id,
        limitation='Submission proves neither convergence nor physical acceptance.',
        next_operation='Collect authentic ' + job_name + ' continuation results and independently evaluate multi-step coupled convergence and physical gates.'
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2)
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--operation-id', default=OPERATION, choices=[OPERATION])
    args = parser.parse_args()
    print(json.dumps(execute(args.workspace, args.output, operation_id=args.operation_id)))
