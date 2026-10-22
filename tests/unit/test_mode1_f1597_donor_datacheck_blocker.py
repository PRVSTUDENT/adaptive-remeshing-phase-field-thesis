"""Unit tests for F1597 candidate donor datacheck blocker audit."""
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.audit_f1597_donor_datacheck_blocker import (
    execute_f1597_donor_datacheck_blocker_audit,
    sha256_file,
    ORIGINAL_DONOR_PATH,
    EXPECTED_ORIGINAL_SHA256,
    CORRECTED_DONOR_PATH,
    EXPECTED_CORRECTED_SHA256,
    PRODUCTION_UEL_PATH,
    EXPECTED_UEL_SHA256
)


@pytest.fixture(scope="module")
def audit_results():
    return execute_f1597_donor_datacheck_blocker_audit()


def test_production_uel_hash():
    """Verify production UEL f42_mixed_uel.for remains 100% bitwise frozen."""
    assert PRODUCTION_UEL_PATH.exists()
    assert sha256_file(PRODUCTION_UEL_PATH) == EXPECTED_UEL_SHA256


def test_original_donor_hash():
    """Verify original candidate donor deck is preserved bitwise unchanged."""
    assert ORIGINAL_DONOR_PATH.exists()
    assert sha256_file(ORIGINAL_DONOR_PATH) == EXPECTED_ORIGINAL_SHA256


def test_corrected_donor_hash():
    """Verify corrected candidate donor deck hash integrity."""
    assert CORRECTED_DONOR_PATH.exists()
    assert sha256_file(CORRECTED_DONOR_PATH) == EXPECTED_CORRECTED_SHA256


def test_blocker_diagnostics_content(audit_results):
    """Verify blocker diagnostic signatures and defect mechanism."""
    diag = audit_results["blocker_diagnostics"]
    assert diag["pre_exit_code"] == 1
    assert diag["fatal_error_count"] == 7
    assert diag["stray_token_identified"] is True
    assert diag["original_equation_header_count"] == 1
    assert diag["corrected_equation_header_count"] == 41


def test_solution_verification_content(audit_results):
    """Verify solver evidence for corrected deck datacheck."""
    sol = audit_results["solution_verification"]
    assert sol["datacheck_exit_code"] == 0
    assert "ANALYSIS DATACHECK COMPLETE" in sol["datacheck_status"]
    assert sol["error_messages"] == 0


def test_submission_withheld_under_governance(audit_results):
    """Verify submission was withheld in strict compliance with repository directive."""
    sub = audit_results["submission_decision"]
    assert sub["submission_executed"] is False
    assert "report the blocker" in sub["reason"]
