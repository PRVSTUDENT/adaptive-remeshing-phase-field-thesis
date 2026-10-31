"""Independent startup/package review and hash-bound controller registration."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.validation.validate_package148_r7_startup import validate


def sha(p):
    return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()


def write(p, obj):
    (ROOT/p).write_text(json.dumps(obj, indent=2)+'\n', encoding='utf-8')


def qualify():
    rel = 'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r7/'
    old = rel.replace('_r7/', '_r6/')
    batch = json.loads((ROOT/rel/'EXECUTION_MANIFEST.json').read_text())
    package = json.loads((ROOT/rel/'PACKAGE_MANIFEST.json').read_text())
    cluster = json.loads((ROOT/'results/validation/package148_r7_cluster_startup.json').read_text())
    assert cluster['status'] == 'PASS' and cluster['history_mappings'] == 28224
    assert json.loads((ROOT/'results/validation/package148_r7_datachecks.json').read_text())['status'] == 'PASS_BOTH'
    assert json.loads((ROOT/'results/validation/package148_r7_history_review.json').read_text())['recomputed_history_mappings'] == 28224
    assert validate(ROOT/rel)['history_mappings'] == 28224
    for name in batch['files']:
        if name.endswith(('.inp', '.inc', '.csv', '.for')):
            assert (ROOT/rel/name).read_bytes() == (ROOT/old/name).read_bytes()
    assert len(package['source_hashes']) == len(package['runtime_source_hashes']) == 4
    assert '--timeout 7200' in (ROOT/rel/'submit_M1_C4_P148_R7.pbs').read_text()
    tests = ['tests/unit/test_package148_r7_startup.py',
             'tests/unit/test_package148_coupled_runtime.py',
             'tests/unit/test_package148_submission_adapter.py',
             'tests/unit/test_mode1_execution_gate.py',
             'tests/unit/test_mode1_f1597_package148_py36_compatibility.py']
    run = subprocess.run([sys.executable, '-m', 'unittest'] +
        [p[:-3].replace('/', '.') for p in tests], cwd=str(ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    write('results/validation/package148_r7_tests.json', dict(returncode=run.returncode, output=run.stdout))
    assert run.returncode == 0, run.stdout
    review = dict(schema=1, verification_passed=True, independent_r7_qualification='PASS',
        review_method='Separate actual-loader and fixed-field card decoder; byte parity against R6 scientific artifacts; no independent-agent review claimed.',
        cluster_startup='PASS', history_mappings=28224, physical_acceptance='UNVERIFIED',
        predecessor='R6 failed before first iteration; technical manifest correction only, no identical retry',
        original_failure='Unreviewed legacy GP ordering; regenerate a distinct candidate revision',
        check_development='Initial 1e-14 card comparison rejected existing %.8e rounding; corrected to exact declared encoding without data changes.',
        staging_repair='Legacy Windows wrapper stripped nested shell quotes; encoded upload commands now use escaped single-quoted hex. No scheduler action occurred.',
        regression_update='First post-registration suite: 63/64 passed; obsolete unknown-revision test expected R7 rejection. Updated unknown revision to R8; R7 now explicitly registered. Initial datacheck receipt capture through local stdin produced no file; repaired with read-only --record-datachecks entrypoint, no Abaqus rerun.',
        scientific_files_unchanged=True, solver_tolerances_unchanged=True,
        timeout=7200, max_outer=25, automatic_retry=False,
        telegram_notification_contract='PENDING_GUARDED_PREFLIGHT', compute_node_delivery='UNRESOLVED')
    review['evidence_sources'] = {p: sha(p) for p in package['runtime_source_hashes']}
    review_path = 'results/validation/package148_r7_execution_review.json'
    write(review_path, review)
    dependencies = dict(package['source_hashes'], **package['runtime_source_hashes'])
    for p in [rel+n for n in batch['files']] + [rel+'EXECUTION_MANIFEST.json',
        'scripts/hpc/Invoke-Mode1Execution.ps1', review_path,
        'results/validation/package148_r6_terminal_evaluation.json',
        'results/validation/package148_r7_cluster_startup.json',
        'results/validation/package148_r7_tests.json',
        'results/validation/package148_r7_datachecks.json',
        'results/validation/package148_r7_history_review.json',
        'scripts/validation/review_package148_r7_history.py',
        'scripts/validation/validate_package148_r7_startup.py']:
        dependencies[p] = sha(p)
    write('scripts/validation/evaluate_mode1_package148_state_transfer_r7.qualification.json',
        dict(schema=1, operation='evaluate_mode1_package148_state_transfer_r7',
             status='QUALIFIED_FOR_PREFLIGHT', dispatch_ready=True,
             canonical_path='scripts/validation/execute_package148_state_transfer.py',
             script_sha256=sha('scripts/validation/execute_package148_state_transfer.py'),
             execution_mode='HPC_PRE_SUBMISSION', execution_adapter='scripts/hpc/Invoke-Mode1Execution.ps1',
             production_uel_sha256=package['frozen_uel_sha256'], manifest=rel+'EXECUTION_MANIFEST.json',
             independent_review=review_path, tests={p: sha(p) for p in tests}, tests_passed=True,
             verification_criteria=dict(required_measurements=['submitted_jobs']),
             scientific_dependencies=dependencies,
             limitation='Startup qualification is not coupled convergence or physical acceptance; no C1-2, retry or tolerance change.'))
    print(run.stdout)


if __name__ == '__main__':
    qualify()
