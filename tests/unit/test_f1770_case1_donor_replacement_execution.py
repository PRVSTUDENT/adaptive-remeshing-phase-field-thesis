"""Unit tests for Task F1770: Case 1 Advancing Coupled Donor Replacement Execution Plan,

Safety-Verified R2 PBS Wrapper & Predeclared Gate Specification.
"""

import hashlib
import os
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

R2_PBS_SCRIPT_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1768_case1_donor", "submit_f1769_case1_donor_r2.pbs"
)
EXPECTED_R2_PBS_SHA = "3A9033581AF1FF5E876FC7367DE6FEC7C94787B0D176B68A8FCCE478AEA78716".lower()


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_immutability():
    """Verify production UEL f42_mixed_uel.for remains bitwise frozen."""
    assert os.path.exists(FROZEN_UEL_PATH), f"UEL not found: {FROZEN_UEL_PATH}"
    actual_sha = compute_sha256(FROZEN_UEL_PATH)
    assert actual_sha == EXPECTED_UEL_SHA, f"UEL hash drift: {actual_sha} != {EXPECTED_UEL_SHA}"


def test_candidate_deck_invariants():
    """Verify candidate production deck is bitwise unmodified and matches 8,718 layered elements."""
    assert os.path.exists(CANDIDATE_DECK_PATH), f"Deck not found: {CANDIDATE_DECK_PATH}"
    actual_sha = compute_sha256(CANDIDATE_DECK_PATH)
    assert actual_sha == EXPECTED_DECK_SHA, f"Deck hash drift: {actual_sha} != {EXPECTED_DECK_SHA}"

    with open(CANDIDATE_DECK_PATH, "r") as f:
        content = f.read()

    assert "N_TOP, 1, 1, 0.0" in content
    assert "N_BOTTOM, 2, 2, 0.0" in content
    assert "MISESERI" in content
    assert "SDV" in content


def test_r2_script_directives_and_atomic_lock_guard():
    """Verify submit_f1769_case1_donor_r2.pbs has atomic directory guard,

    fails closed on pre-existing Abaqus lock, and contains ZERO unconditional rm -f lock deletions.
    """
    assert os.path.exists(R2_PBS_SCRIPT_PATH), f"R2 script not found: {R2_PBS_SCRIPT_PATH}"
    actual_sha = compute_sha256(R2_PBS_SCRIPT_PATH)
    assert actual_sha == EXPECTED_R2_PBS_SHA, f"R2 script hash mismatch: {actual_sha} != {EXPECTED_R2_PBS_SHA}"

    with open(R2_PBS_SCRIPT_PATH, "r") as f:
        content = f.read()

    # 1. Atomic POSIX directory lock guard
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
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content


def test_failed_predecessor_job_provenance():
    """Verify that HPC_JOB_LEDGER.csv accurately records failed Job 1423603.mmaster02 with Exit 1."""
    hpc_ledger_path = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
    assert os.path.exists(hpc_ledger_path)
    with open(hpc_ledger_path, "r") as f:
        lines = f.readlines()

    # Find Job 1423603
    job_lines = [l for l in lines if "1423603.mmaster02" in l]
    assert len(job_lines) >= 2, f"Expected at least 2 entries for 1423603 (SUBMITTED + FAILED), found {len(job_lines)}"
    failed_entry = [l for l in job_lines if "FAILED" in l]
    assert len(failed_entry) == 1, f"Missing or duplicate FAILED entry for 1423603: {failed_entry}"
    assert "FAILED,1,CASE1_DONOR_SOLVER_COLLIDED_WITH_SCRIPT_LOCK_GUARD" in failed_entry[0]
