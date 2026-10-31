"""Verify Turn381 evidence before issuing a distinct corrected closeout receipt.

Original preparation, solver data, marking artifact and final response stay intact.
No scheduler operations or numerical assumption changes.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RUN = 'ccdabd62-f135-46b0-bc02-e04e0db15759'
OUT = 'results/validation/turn381_receipt_reconciliation/'
AUDIT = 'models/pandey_kumar_mode1/153_c4_companion_miseseri/c4_package153_miseseri_audit.json'
CSV = AUDIT.replace('c4_package153_miseseri_audit.json', 'c4_package153_companion_miseseri_distribution.csv')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def summary_from_rows(rows):
    assert len(rows) == 7056
    assert sorted(int(r['element_id']) for r in rows) == list(range(1, 7057))
    for row in rows:
        eri, avg, eta = [float(row[k]) for k in ('miseseri_kNmm2', 'misesavg_kNmm2', 'eta_relative_error')]
        assert all(math.isfinite(v) for v in (eri, avg, eta))
        assert eri >= 0 and avg > 0
        assert math.isclose(eta, eri / avg if avg > 1e-6 else 0., rel_tol=1e-12, abs_tol=1e-15)
    peak = max(rows, key=lambda r: float(r['miseseri_kNmm2']))
    relative = max(rows, key=lambda r: float(r['eta_relative_error']))
    count = sum(float(r['eta_relative_error']) >= .15 for r in rows)

    def details(row):
        return dict(element_id=int(row['element_id']),
                    miseseri_kNmm2=float(row['miseseri_kNmm2']),
                    misesavg_kNmm2=float(row['misesavg_kNmm2']),
                    eta=float(row['eta_relative_error']),
                    centroid_mm=dict(x=float(row['x_mm']), y=float(row['y_mm'])))
    return dict(job_name='M1_C4_COMPANION_MISESERI', pbs_job_id='1419101.mmaster02',
                loading_state=dict(prescribed_u2_mm=.002,
                    state_description='Package 153 C4 Companion Continuum Model for Stage C1-2 Target State'),
                total_elements=len(rows), peak_miseseri=details(peak),
                peak_relative_error=details(relative),
                refinement_metrics=dict(threshold_eta=.15, elements_above_threshold=count,
                    pct_above_threshold=count/len(rows)*100.,
                    adaptation_recommendation='ADVANCE_CYCLE_C5_REFINEMENT' if count else 'CONVERGED_TERMINATE'))


def verify(root=ROOT):
    original = json.loads((root/(OUT+'original_preparation.json')).read_text())
    mismatches = []
    for name, expected in original['evidence_sources'].items():
        actual = sha(root/name)
        if actual != expected:
            mismatches.append(dict(path=name, expected=expected, actual=actual))
    assert len(mismatches) == 1 and mismatches[0]['path'] == AUDIT, mismatches
    # CSV bytes are still bound to the original receipt; reproduce every audit
    # field from those immutable extracted values rather than trusting a rehash.
    with (root/CSV).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    reproduced = summary_from_rows(rows)
    actual = json.loads((root/AUDIT).read_text())
    assert reproduced == actual, 'Audit differs scientifically from original hash-bound CSV'
    assert reproduced['refinement_metrics']['elements_above_threshold'] == 266
    return original, mismatches, reproduced


def build():
    original, mismatches, reproduced = verify()
    tests = ['tests/unit/test_turn381_receipt_reconciliation.py',
             'tests/unit/test_package153_companion_miseseri.py',
             'tests/unit/test_c4_refinement_marking_interface.py']
    run = subprocess.run([sys.executable, '-m', 'pytest', '-q'] + tests,
                         cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True)
    test_path = ROOT/(OUT+'tests.json')
    test_path.write_text(json.dumps(dict(returncode=run.returncode, output=run.stdout), indent=2)+'\n')
    assert run.returncode == 0, run.stdout
    review = dict(schema=1, verification_passed=True, status='INVESTIGATION_COMPLETE',
        finding='Turn381 fallback receipt fails solely on stale Package153 audit byte hash; all audit fields independently reproduced from the original hash-bound 7056-row CSV. Final response lacks Finished. No numerical result changed.',
        original_run_id=RUN, mismatches=mismatches, audit_semantic_reconstruction='PASS_ALL_FIELDS',
        mutation_writer='UNESTABLISHED; current audit is the committed blob, not an uncommitted local change',
        elements=7056, marked_elements=266, numerical_assumptions_changed=False,
        scientific_limitations='P152 R2 Step1 history stopping criterion failed; C1-2 remains unaccepted. C5 transfer/continuation remains dependent. Original marking contains old audit byte hash and needs fresh provenance qualification before downstream execution.',
        tests=run.stdout)
    review_path = ROOT/(OUT+'review.json')
    review_path.write_text(json.dumps(review, indent=2)+'\n')
    corrected = dict(original)
    corrected['finding'] += ' Closeout receipt corrected only after independent audit reconstruction from the original CSV; original receipt preserved.'
    corrected['derived_from'] = 'results/validation/preparation-'+RUN+'.json'
    corrected['derived_from_sha256'] = sha(ROOT/corrected['derived_from'])
    corrected['correction_review'] = OUT+'review.json'
    corrected['evidence_sources'] = {p: sha(ROOT/p) for p in original['evidence_sources']}
    for p in [OUT+'original_preparation.json', OUT+'original_bootstrap.json',
              OUT+'review.json', OUT+'tests.json',
              'scripts/validation/reconcile_turn381_receipt.py'] + tests:
        corrected['evidence_sources'][p] = sha(ROOT/p)
    target = ROOT/(OUT+'corrected_preparation.json')
    if target.exists():
        raise ValueError('Preserve existing correction; do not overwrite')
    target.write_text(json.dumps(corrected, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify-only']:
        _, mismatches, summary = verify()
        print(json.dumps(dict(mismatches=mismatches, reconstructed=summary), indent=2))
    else:
        build()
