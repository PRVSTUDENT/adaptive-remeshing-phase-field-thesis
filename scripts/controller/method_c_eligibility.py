"""Inactive-by-default, independently reviewed Method C eligibility policy gate.

No solver or scheduler mutations. Approval attests a procedure/policy, never a
job permission. Existing once-only execution remains the only submission path.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import os
import sys
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.controller.review_dispatcher import canonical, inside, read, sha, verify_receipt
from scripts.hpc.mode1_execution_gate import validate_manifest

POLICY = 'project_coordination/policies/method_c_serial_continuation_v1.json'
ACTIVATION = 'project_coordination/policies/method_c_serial_continuation_v1.review.json'


def policy_request(root):
    policy = read(root/POLICY)
    if not policy or policy['version'] != 1 or policy['author'] == 'ChatGPT-independent-review':
        raise ValueError('INVALID_POLICY_IDENTITY')
    sources = [POLICY, 'scripts/controller/method_c_eligibility.py',
               'scripts/controller/Invoke-MethodCEligibleExecution.ps1',
               'scripts/validation/evaluate_package157_r6_checkpoint.py',
               'scripts/controller/review_dispatcher.py',
               'scripts/hpc/mode1_execution_gate.py',
               'scripts/hpc/Invoke-Mode1Execution.ps1',
               '.agents/scripts/Invoke-GuardedSsh.ps1']
    for name, digest in policy['pinned_sources'].items():
        if sha(inside(root,name)) != digest:
            raise ValueError('POLICY_SOURCE_CHANGED_REVIEW_REQUIRED: '+name)
        sources.append(name)
    hashes = {name:sha(inside(root,name)) for name in sources}
    return dict(operation_id=policy['id'],correlation_id=policy['review_correlation_id'],
        definition=dict(author=policy['author']), hashes=hashes,
        fingerprint=hashlib.sha256(canonical(dict(policy=policy,hashes=hashes))).hexdigest().upper(),
        required_decisions=['APPROVE','REJECT','INSUFFICIENT_EVIDENCE'])


def active_policy(root, key):
    request = policy_request(root)
    receipt = read(root/ACTIVATION)
    if not receipt:
        raise ValueError('POLICY_INDEPENDENT_ACTIVATION_MISSING')
    if not key or not Path(key).is_file() or Path(key).resolve().is_relative_to(root):
        raise ValueError('EXTERNALLY_CONTROLLED_REVIEW_PROVENANCE_UNAVAILABLE')
    decision = verify_receipt(receipt, request, key)
    if decision['decision'] != 'APPROVE':
        raise ValueError('POLICY_NOT_INDEPENDENTLY_APPROVED')
    return read(root/POLICY)


def scientific_receipt(root, path, checkpoint_hash):
    receipt = read(inside(root,path))
    if (not receipt or receipt.get('kind') != 'SAVED_SOLVER_CHECKPOINT_ASSESSMENT' or
            receipt.get('physical_acceptance') != 'PASS'):
        raise ValueError('PREDECESSOR_PHYSICAL_ACCEPTANCE_REQUIRED')
    if not receipt.get('gates') or not all(v is True for v in receipt['gates'].values()):
        raise ValueError('ALL_PREDECLARED_SCIENTIFIC_GATES_REQUIRED')
    for name,digest in receipt['sources'].items():
        if sha(inside(root,name)) != digest:
            raise ValueError('STALE_SCIENTIFIC_EVIDENCE: '+name)
    evaluator='scripts/validation/evaluate_package157_r6_checkpoint.py'
    if receipt['sources'].get(evaluator) != sha(root/evaluator):
        raise ValueError('PROTECTED_EVALUATOR_BINDING_REQUIRED')
    checkpoints=[h for p,h in receipt['sources'].items() if p.endswith('/initial_checkpoint_01.json')]
    if checkpoints != [checkpoint_hash]:
        raise ValueError('PREDECESSOR_CHECKPOINT_IDENTITY_REQUIRED')
    # Never trust Gemini-written PASS flags. Recompute the protected scientific
    # evaluator against the archived actual solver evidence on every use.
    from scripts.validation.evaluate_package157_r6_checkpoint import assess
    if canonical(assess(root)) != canonical(receipt):
        raise ValueError('SCIENTIFIC_RECEIPT_NOT_REPRODUCIBLE')
    return receipt


def eligible(root, operation, acceptance, key=None):
    root=Path(root).resolve()
    policy=active_policy(root,key)  # No unsigned fallback, no author self-activation.
    if operation not in policy['operation_ids']:
        raise ValueError('NEW_OPERATION_CLASS_REQUIRES_INDEPENDENT_REVIEW')
    definition=read(inside(root,'project_coordination/operation_definitions/'+operation+'.json'))
    batch,manifest_hash,_=validate_manifest(inside(root,definition['manifest']),root)
    if (batch['adapter'] != 'mode1-qualified-batch-v2' or len(batch['jobs']) != 1 or
            batch['jobs'][0]['cpus'] != 1 or batch['jobs'][0]['memory_gb'] > 16 or
            batch['jobs'][0]['walltime_hours'] > 8 or batch['automatic_retry'] is not False):
        raise ValueError('ORIGINAL_SERIAL_MODE1_ENVELOPE_REQUIRED')
    if batch['files'].get('f42_mixed_uel.for','').upper() != policy['frozen_uel_sha256']:
        raise ValueError('FROZEN_UEL_CHANGED')
    for name,digest in batch['runtime_source_hashes'].items():
        if policy['pinned_sources'].get(name) != digest.upper() or sha(root/name) != digest.upper():
            raise ValueError('UNREVIEWED_NUMERICAL_RUNTIME: '+name)
    package=inside(root,definition['manifest']).parent
    checkpoint=read(package/'initial_checkpoint_01.json')
    acceptance_result=scientific_receipt(root,acceptance,sha(package/'initial_checkpoint_01.json'))
    controls=read(package/'PACKAGE_MANIFEST.json')
    targets=controls['targets_mm']
    if (len(targets)!=1 or controls['baseline_uy_mm'] != checkpoint['target_uy_mm'] or
            not Decimal('0') < Decimal(str(targets[0]))-Decimal(str(checkpoint['target_uy_mm'])) <= Decimal(str(policy['max_increment_mm'])) or
            controls['max_outer'] > policy['max_outer']):
        raise ValueError('UNREVIEWED_CONTINUATION_CONTROLS')
    return dict(status='SCIENTIFICALLY_ELIGIBLE_PENDING_LIVE_PREFLIGHT',operation_id=operation,
        manifest=definition['manifest'],manifest_sha256=manifest_hash,
        policy_sha256=sha(root/POLICY),acceptance_sha256=sha(root/acceptance),
        predecessor_physical_acceptance=acceptance_result['physical_acceptance'],
        execution_adapter='scripts/hpc/Invoke-Mode1Execution.ps1',automatic_retry=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workspace',default=str(ROOT))
    parser.add_argument('--operation-id');parser.add_argument('--acceptance')
    parser.add_argument('--policy-review-request',action='store_true')
    args=parser.parse_args();root=Path(args.workspace).resolve()
    try:
        result=policy_request(root) if args.policy_review_request else eligible(root,args.operation_id,args.acceptance,os.environ.get('PRV_REVIEW_BRIDGE_PUBLIC_KEY'))
        print(json.dumps(result,indent=2))
    except Exception as error:
        print(json.dumps(dict(status='BLOCKED',reason=str(error))));sys.exit(2)
