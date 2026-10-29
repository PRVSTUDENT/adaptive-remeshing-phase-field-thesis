"""Review packet builder. Never registers or approves its own implementation."""
import argparse
import json
from pathlib import Path
from evaluate_package146_package147_results import compute_file_sha256, OPERATION, FROZEN_UEL_SHA256

WORKSPACE = Path(__file__).resolve().parents[2]
EXPECTED_UEL_SHA256 = FROZEN_UEL_SHA256
TARGET_DISPLACEMENT = 0.0018003125442191958


def compile_review_intake(report_path=None, test_receipt_path=None):
    paths = ['scripts/validation/evaluate_package146_package147_results.py',
             'scripts/validation/evaluate_package146_package147_evaluation_spec.py',
             'scripts/validation/extract_package146147_odb.py',
             'scripts/validation/audit_h55_refinement_only_geometry.py',
             'tests/unit/test_mode1_f1597_package146_147_evaluation_definition.py']
    paths += [str(p.relative_to(WORKSPACE)).replace('\\', '/') for p in sorted(
        (WORKSPACE/'tests/fixtures/package146147').iterdir()) if p.is_file()]
    sources = {p: compute_file_sha256(WORKSPACE/p) for p in paths}
    report = json.loads(Path(report_path).read_text()) if report_path else {}
    receipt = json.loads(Path(test_receipt_path).read_text()) if test_receipt_path else {}
    bound = bool(receipt) and all(receipt.get('sources', {}).get(p) == h for p, h in sources.items())
    tests_ok = bound and receipt.get('failures') == 0 and receipt.get('errors') == 0 and receipt.get('skipped') == 0 and receipt.get('tests_run', 0) > 0
    evidence_ok = bool(report_path) and bool(report.get('comparisons')) and all(
        report.get('packages', {}).get(str(p), {}).get('status') == 'AUTHENTICATED_MEASUREMENTS' for p in (146, 147))
    report_bound = bool(report_path) and receipt.get('result_report_sha256') == compute_file_sha256(report_path)
    ready = bool(tests_ok and evidence_ok and report_bound)
    return dict(operation_id=OPERATION, source_hashes=sources, tests_bound=bound,
                tests_passed=bool(tests_ok), genuine_result_evidence_bound=bool(evidence_ok and report_bound),
                verification_passed=ready, registration_status='NOT_REGISTERED', executable_in_current_scope=False,
                review_status='READY_FOR_INDEPENDENT_REVIEW' if ready else 'REVIEW_EVIDENCE_INCOMPLETE',
                outstanding_limitations=['Intermediate nodal U3 path not recorded: full nodal irreversibility unverified',
                                        'SDV2 exports trial GP history, not a committed-array preservation proof',
                                        'Continuous-mesh sensitivity is not nonmatching transfer acceptance',
                                        'Independent review required before any controller registration'],
                scientific_acceptance=False, frozen_uel_sha256=FROZEN_UEL_SHA256)


audit_evidence = compile_review_intake
if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--report'); p.add_argument('--test-receipt')
    a = p.parse_args()
    print(json.dumps(compile_review_intake(a.report, a.test_receipt), indent=2, allow_nan=False))
