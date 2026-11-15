"""Unit tests for Task F1769: Case 1 Advancing Coupled Donor Execution Plan,

Boundary Condition Audit & Acceptance Gate Specification.
"""

import hashlib
import os
import re
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6".lower()

CANDIDATE_DECK_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1768_case1_donor", "PK_F1768_CASE_1_COARSE_COUPLED.inp"
)
EXPECTED_DECK_SHA = "7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6".lower()

PBS_SCRIPT_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1768_case1_donor", "submit_f1768_case1_donor.pbs"
)
EXPECTED_PBS_SHA = "B01A50AF39083E315EE167C6CE5469EC9F8B0D026E9678DFD75D2AA3B191ADA6".lower()

REF_DECK_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "01_standard_pfm_reference", "PK_MODE1_STANDARD_PFM.inp"
)


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_immutability():
    """Verify production UEL f42_mixed_uel.for is bitwise frozen."""
    assert os.path.exists(FROZEN_UEL_PATH), f"UEL not found: {FROZEN_UEL_PATH}"
    actual_sha = compute_sha256(FROZEN_UEL_PATH)
    assert actual_sha == EXPECTED_UEL_SHA, f"UEL hash drift: {actual_sha} != {EXPECTED_UEL_SHA}"


def test_candidate_deck_integrity_and_bc_concordance():
    """Verify candidate production deck hash, element count, and top-edge BC."""
    assert os.path.exists(CANDIDATE_DECK_PATH), f"Deck not found: {CANDIDATE_DECK_PATH}"
    actual_sha = compute_sha256(CANDIDATE_DECK_PATH)
    assert actual_sha == EXPECTED_DECK_SHA, f"Deck hash mismatch: {actual_sha} != {EXPECTED_DECK_SHA}"

    with open(CANDIDATE_DECK_PATH, "r") as f:
        content = f.read()

    # Verify top edge boundary condition
    assert "N_TOP, 1, 1, 0.0" in content, "Missing N_TOP, 1, 1, 0.0 boundary condition"
    assert "N_BOTTOM, 2, 2, 0.0" in content, "Missing N_BOTTOM, 2, 2, 0.0 boundary condition"
    assert "N_PIN, 1, 1, 0.0" in content, "Missing N_PIN, 1, 1, 0.0 boundary condition"

    # Verify 3-layer structure
    assert "*ELEMENT, TYPE=U1" in content or "*ELEMENT, TYPE=U1" in content.upper()
    assert "*ELEMENT, TYPE=U2" in content or "*ELEMENT, TYPE=U2" in content.upper()
    assert "*ELEMENT, TYPE=CPE4" in content or "*ELEMENT, TYPE=CPE4" in content.upper()

    # Verify field outputs
    assert "MISESERI" in content
    assert "SDV" in content


def test_reference_mode1_bc_concordance():
    """Verify that authoritative reference deck PK_MODE1_STANDARD_PFM.inp contains identical BCs."""
    assert os.path.exists(REF_DECK_PATH), f"Reference deck not found: {REF_DECK_PATH}"
    with open(REF_DECK_PATH, "r") as f:
        ref_content = f.read()

    assert "N_TOP, 1, 1, 0.0" in ref_content, "Reference deck lacks N_TOP, 1, 1, 0.0"
    assert "N_BOTTOM, 2, 2, 0.0" in ref_content, "Reference deck lacks N_BOTTOM, 2, 2, 0.0"
    assert "N_PIN, 1, 1, 0.0" in ref_content, "Reference deck lacks N_PIN, 1, 1, 0.0"


def test_pbs_script_directives_and_notifications():
    """Verify PBS execution script directives, resource bounds, and notifications."""
    assert os.path.exists(PBS_SCRIPT_PATH), f"PBS script not found: {PBS_SCRIPT_PATH}"
    actual_sha = compute_sha256(PBS_SCRIPT_PATH)
    assert actual_sha == EXPECTED_PBS_SHA, f"PBS hash mismatch: {actual_sha} != {EXPECTED_PBS_SHA}"

    with open(PBS_SCRIPT_PATH, "r") as f:
        pbs_content = f.read()

    # Check resource directives
    assert "#PBS -l select=1:ncpus=1:mem=8gb" in pbs_content
    assert "#PBS -l walltime=02:00:00" in pbs_content
    assert "#PBS -q entry_imfdfkmq" in pbs_content
    assert "#PBS -m abe" in pbs_content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs_content

    # Check lock guard and scratch space check
    assert "${JOB_NAME}.lck" in pbs_content
    assert "AVAIL_KB" in pbs_content


def test_pbs_r2_atomic_lock_guard_and_safe_reconciliation():
    """Verify that submit_f1769_case1_donor_r2.pbs implements atomic locking,

    fails closed on pre-existing Abaqus locks, and contains ZERO unconditional rm -f lock deletions.
    """
    r2_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1768_case1_donor", "submit_f1769_case1_donor_r2.pbs"
    )
    assert os.path.exists(r2_path), f"R2 script not found: {r2_path}"
    with open(r2_path, "r") as f:
        content = f.read()

    # 1. Atomic directory guard
    assert 'LOCK_GUARD_DIR="${RUN_DIR}/${JOB_NAME}.pbs_guard_d"' in content
    assert 'mkdir "${LOCK_GUARD_DIR}"' in content
    assert 'rmdir "${LOCK_GUARD_DIR}"' in content

    # 2. Fail closed on pre-existing Abaqus lock
    assert 'if [ -e "${RUN_DIR}/${JOB_NAME}.lck" ]; then' in content
    assert 'echo "ERROR: Pre-existing Abaqus lock file ${JOB_NAME}.lck detected. Failing closed."' in content

    # 3. Strictly ZERO unconditional rm -f of Abaqus lock files
    assert 'rm -f "${JOB_NAME}.lck"' not in content, "Unsafe unconditional Abaqus lock deletion detected"
    assert 'rm -f PK_F1768_C1_DONOR.lck' not in content, "Unsafe unconditional lock deletion detected"
    assert 'rm -f *.lck' not in content, "Unsafe wildcard lock deletion detected"

    # 4. Resource bounds
    assert "#PBS -l select=1:ncpus=1:mem=8gb" in content
    assert "#PBS -l walltime=02:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content


