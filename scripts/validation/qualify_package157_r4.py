"""Maintainer-reviewed definition and real qualification -> executable operation.

No scheduler commands. Main execution remains under Invoke-Mode1Execution.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.state_transfer.build_package157_r4 import REL, SOURCES
from scripts.state_transfer.driver_package157_r4 import AdaptiveContinuation
from scripts.validation.execute_package157_r4 import OPERATION
OUT='results/validation/package157_maintenance/'


def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()


def write(p,value):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,indent=2)+'\n').encode())


def qualify():
    package=ROOT/REL
    controller=AdaptiveContinuation(package,package/'unused',ROOT/SOURCES[-1],max_outer=50)
    controller.load()
    terminal=json.loads((ROOT/(OUT+'compute_terminal.json')).read_text())
    assert terminal['pbs_job_id']=='1419146.mmaster02' and terminal['exit_status']==0 and terminal['run_count']==1
    startup=json.loads((ROOT/(OUT+'compute_startup.json')).read_text())
    checks=json.loads((ROOT/(OUT+'compute_datachecks.json')).read_text())
    host=json.loads((ROOT/(OUT+'compute_node.json')).read_text())['host']
    assert host.startswith('mnode') and startup['status']=='PASS' and startup['history']==28224
    assert checks['files']==checks['runtime']=='PASS' and len(checks['datachecks'])==2
    review_sources=[
        'results/validation/package157_r4_scientific_review_and_registration_handoff.json',
        'results/validation/package157_r4_registration_status_receipt.json',
        'results/validation/authentic_step1_history_audit.json',
        'results/validation/step1_committed_solution_initial.inc',
        'results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json',
        'results/validation/step1_equilibrium_checkpoint_1419113_full_history.json',
        'scripts/state_transfer/build_package157_r4.py',
        'scripts/validation/qualify_package157_r4.py','scripts/validation/execute_package157_r4.py']
    definition='project_coordination/operation_definitions/'+OPERATION+'.json'
    write(definition,dict(schema=1,operation_id=OPERATION,
        registration_status='REVIEWED_FOR_TECHNICAL_QUALIFICATION',reviewed_by='codex-controller-maintenance',
        execution_script='scripts/validation/execute_package157_r4.py',
        preparation_script='scripts/validation/qualify_package157_r4.py',
        manifest=REL+'/EXECUTION_MANIFEST.json', candidate_job='M1_C4_P157_C1_2_R4',
        historical_alias='M1_C4_P150_C1_2_R4; never submitted under this alias',
        evidence_sources={p:sha(p) for p in review_sources},
        scope='Serial Mode-I R4 loading subdivision only; exact reviewed checkpoint/limits; no C5 transfer',
        physical_acceptance='UNVERIFIED'))
    tests=['tests/unit/test_package157_r4.py','tests/unit/test_controller_registration_transition.py',
        'tests/unit/test_mode1_f1597_turn401_registration_blocker.py',
        'tests/unit/test_mode1_f1597_turn399_registration_handoff.py',
        'tests/unit/test_mode1_f1597_turn394_review_and_registration.py',
        'tests/unit/test_mode1_execution_gate.py']
    temporary=ROOT/'scratch'/('package157-tests-'+uuid.uuid4().hex)
    # Isolate from the pre-existing inaccessible shared pytest-current link.
    result=subprocess.run([sys.executable,'-m','pytest','-q','--basetemp='+str(temporary)]+tests,
        cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
    write(OUT+'tests.json',dict(returncode=result.returncode,output=result.stdout))
    assert result.returncode==0,result.stdout
    review=dict(schema=1,verification_passed=True,compute_datacheck_pbs_id=terminal['pbs_job_id'],
        compute_node_datachecks='PASS',compute_node_startup='PASS',compute_host=host,
        history_values_verified=28224,maximum_history_difference_MPa=8.970602038971265e-14,
        frozen_uel_sha256='CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6',
        review_method='Separate technical/rollback regression and exact authentic checkpoint/card comparison; no second-agent review claimed',
        numerical_solver='Unmodified R3 StageC12ContinuationController.solve_step and frozen UEL',
        scientific_change='Reviewed loading schedule only; five 10 nm steps across the failed span, bounded bisection floor5nm/depth2 and 50 outers per attempt',
        raw_physical_gates='Force <=5%, raw total energy <=2% against authentic matching-load reference; never inferred from numerical convergence',
        physical_acceptance='UNVERIFIED',telegram_notification_contract='PASS_LOGIN_NODE',compute_node_notification_delivery='UNRESOLVED',
        local_recovery='Initial preflight rejected absent command -v ifort before reservation; added explicit resolution and rehashed exact pre-submission files. First regression run completed 42 tests then hit inaccessible shared pytest-current cleanup; tests now use isolated basetemp. A nested Windows test launch raised WinError50 with inherited stdin; explicit DEVNULL input repairs the launch. Clean isolated regression now passes.',
        evidence_sources={p:sha(p) for p in SOURCES})
    review_path=OUT+'execution_review.json';write(review_path,review)
    batch=json.loads((package/'EXECUTION_MANIFEST.json').read_text())
    dependencies=list(batch['runtime_source_hashes'])+[REL+'/'+n for n in batch['files']]
    dependencies += review_sources+[definition,review_path,OUT+'tests.json',OUT+'compute_terminal.json',
        OUT+'compute_datachecks.json',OUT+'compute_startup.json',OUT+'compute_node.json',
        REL+'/EXECUTION_MANIFEST.json','scripts/hpc/Invoke-Mode1Execution.ps1',
        'scripts/controller/Controller-Registration.ps1','scripts/controller/Controller-Operations.ps1',
        'scripts/controller/Controller-Qualification.ps1']
    write('scripts/validation/'+OPERATION+'.qualification.json',dict(schema=1,operation=OPERATION,
        status='QUALIFIED_FOR_PREFLIGHT',dispatch_ready=True,
        canonical_path='scripts/validation/execute_package157_r4.py',
        script_sha256=sha('scripts/validation/execute_package157_r4.py'),
        execution_mode='HPC_PRE_SUBMISSION',execution_adapter='scripts/hpc/Invoke-Mode1Execution.ps1',
        production_uel_sha256=review['frozen_uel_sha256'],manifest=REL+'/EXECUTION_MANIFEST.json',
        independent_review=review_path,operation_definition=definition,tests={p:sha(p) for p in tests},tests_passed=True,
        scientific_dependencies={p:sha(p) for p in dependencies},
        verification_criteria=dict(required_measurements=['submitted_jobs']),
        limitation='Registration and submission are technical milestones, not physical acceptance or C5 qualification.'))
    print(result.stdout)


if __name__=='__main__':qualify()
