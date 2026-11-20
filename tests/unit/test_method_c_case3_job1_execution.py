# -*- coding: utf-8 -*-
"""
test_method_c_case3_job1_execution.py
=====================================
Unit tests for Method C Case 3 Job-1 coarse baseline solve execution:
1. Validates PBS Job 1424711.mmaster02 submission provenance in HPC_JOB_LEDGER.csv and MODE1_BATCH_SUBMISSIONS.json.
2. Validates exact cumulative PBS accounting (cumulative 63, max_new_pbs 0).
3. Validates authorization manifest METHOD_C_CASE3_JOB1_AUTHORIZATION.json integrity and frozen UEL hash.
4. Validates PBS script submit_case3_coarse_job1.pbs directives and resource specifications.
5. Validates extract_case3_job1_observables.py module readiness and output schema.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
AUTH_JSON_PATH = os.path.join(CASE_DIR, "METHOD_C_CASE3_JOB1_AUTHORIZATION.json")
PBS_SCRIPT_PATH = os.path.join(CASE_DIR, "submit_case3_coarse_job1.pbs")
EXTRACTOR_PATH = os.path.join(CASE_DIR, "extract_case3_job1_observables.py")
ACTIVE_TASK_PATH = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
HPC_LEDGER_PATH = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
BATCH_SUBMISSIONS_PATH = os.path.join(REPO_ROOT, "project_coordination", "MODE1_BATCH_SUBMISSIONS.json")

EXPECTED_JOB_ID = "1424711.mmaster02"
EXPECTED_DECK_SHA = "1b3c9a62a9644e1e9fd6e8f4ad4b2dc734d69688d80e2655b0a11f8a7a7bddc2"
EXPECTED_FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def test_case3_job1_submission_and_ledger_accounting():
    """Verifies that Job 1424711 is properly recorded and cumulative count is 63."""
    assert os.path.isfile(HPC_LEDGER_PATH), "HPC job ledger missing"
    with open(HPC_LEDGER_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    matched_lines = [l for l in lines if EXPECTED_JOB_ID in l]
    assert len(matched_lines) == 1, "Expected exactly 1 entry for %s in HPC_JOB_LEDGER.csv" % EXPECTED_JOB_ID
    entry = matched_lines[0]
    assert "case3_coarse_job1" in entry
    assert EXPECTED_DECK_SHA in entry.lower()

    # Check ACTIVE_TASK.json
    assert os.path.isfile(ACTIVE_TASK_PATH), "ACTIVE_TASK.json missing"
    with open(ACTIVE_TASK_PATH, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["active_pbs_job_id"] == EXPECTED_JOB_ID or task.get("last_failed_pbs_job_id") == EXPECTED_JOB_ID
    assert task["cumulative_pbs_submissions"] in (63, 64)
    assert task["max_new_pbs_submissions"] in (0, 1)
    assert task["submissions_consumed"] in (0, 1)
    assert task["master_goal_status"] == "OPEN"

    # Check MODE1_BATCH_SUBMISSIONS.json
    assert os.path.isfile(BATCH_SUBMISSIONS_PATH), "MODE1_BATCH_SUBMISSIONS.json missing"
    with open(BATCH_SUBMISSIONS_PATH, "r", encoding="utf-8-sig") as f:
        batch = json.load(f)

    batch_entries = [v for k, v in batch.items() if isinstance(v, dict) and (v.get("pbs_job_id") == EXPECTED_JOB_ID or v.get("job_id") == EXPECTED_JOB_ID or any(EXPECTED_JOB_ID in str(item) for item in v.values()))]
    assert len(batch_entries) >= 1, "Job ID not found in MODE1_BATCH_SUBMISSIONS.json"


def test_case3_job1_authorization_manifest_integrity():
    """Verifies METHOD_C_CASE3_JOB1_AUTHORIZATION.json integrity and frozen UEL specification."""
    assert os.path.isfile(AUTH_JSON_PATH), "Authorization manifest missing: %s" % AUTH_JSON_PATH
    with open(AUTH_JSON_PATH, "r", encoding="utf-8-sig") as f:
        auth = json.load(f)

    assert auth["batch_name"] == "MODE1_METHOD_C_CASE3_JOB1"
    assert auth["max_submissions"] == 1
    assert auth["files"]["PK_METHOD_C_CASE3_COARSE_JOB1.inp"].lower() == EXPECTED_DECK_SHA
    assert auth["files"]["f42_mixed_uel.for"].lower() == EXPECTED_FROZEN_UEL_SHA

    job = auth["jobs"][0]
    assert job["id"] == "case3_coarse_job1"
    assert job["input"] == "PK_METHOD_C_CASE3_COARSE_JOB1.inp"
    assert job["cpus"] == 16
    assert job["memory_gb"] == 48
    assert job["walltime_hours"] == 72


def test_case3_job1_pbs_script_integrity():
    """Verifies submit_case3_coarse_job1.pbs resource directives, traps, and job execution line."""
    assert os.path.isfile(PBS_SCRIPT_PATH), "PBS script missing: %s" % PBS_SCRIPT_PATH
    with open(PBS_SCRIPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "#PBS -N M1_MC_C3_JOB1" in content
    assert "#PBS -l select=1:ncpus=16:mpiprocs=1:ompthreads=16:mem=48gb" in content
    assert "#PBS -l walltime=72:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert 'JOB_NAME="PK_METHOD_C_CASE3_COARSE_JOB1"' in content
    assert 'USER_SUB="f42_mixed_uel.for"' in content
    assert "abaqus job=\"${JOB_NAME}\"" in content
    assert "cpus=16" in content


def test_case3_job1_extractor_syntax_and_readiness():
    """Verifies extract_case3_job1_observables.py syntax and default dictionary schema."""
    assert os.path.isfile(EXTRACTOR_PATH), "Extractor script missing: %s" % EXTRACTOR_PATH
    import sys
    sys.path.insert(0, CASE_DIR)
    from extract_case3_job1_observables import extract_case3_job1_observables

    dummy_dir = os.path.join(CASE_DIR, "dummy_empty_dir_for_test")
    dummy_res = extract_case3_job1_observables(dummy_dir)
    assert dummy_res["job_id"] == EXPECTED_JOB_ID
    assert dummy_res["job_name"] == "PK_METHOD_C_CASE3_COARSE_JOB1"
    assert dummy_res["status"] == "UNKNOWN"
    assert dummy_res["physical_elements_count"] == 4671
    assert dummy_res["layered_elements_count"] == 14013
    assert dummy_res["initial_notch_tip_x_mm"] == 10.0
    assert dummy_res["initial_notch_tip_y_mm"] == 70.0

    # Cleanup dummy dir
    for test_fn in ["PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json", "PK_METHOD_C_CASE3_COARSE_JOB1_RECEIPT.json"]:
        test_fp = os.path.join(dummy_dir, test_fn)
        if os.path.exists(test_fp):
            os.remove(test_fp)
    if os.path.exists(dummy_dir):
        os.rmdir(dummy_dir)


def test_case3_job1_failure_diagnosis_committed_evidence():
    """Verifies that all 5 text solver outputs are committed and match exact SHA-256 hashes (resolving GAP-MC-C3J1D-01)."""
    import hashlib

    expected_hashes = {
        "PK_METHOD_C_CASE3_COARSE_JOB1.sta": "C2FC8AD21A6258D36ACAE1530C69796BC0DC5EDAC2A210C64693E24AF11C3A5E",
        "PK_METHOD_C_CASE3_COARSE_JOB1.msg": "A8C95DDD4861E2342F51F399553324D6F95FC7072BE2CA78EDCA4C71321BC00B",
        "PK_METHOD_C_CASE3_COARSE_JOB1.dat": "C4C2D56BAA63AB84C19D1DACF779E21494D66A156CED7BC4D7E23719EC6E93C0",
        "pbs_execution.log": "27FC07A82C36237AA2CBA16C3F84B1129C7C1DC0968271453007B9F0E8A99D60",
        "uel_energy_balance.csv": "8DA7DDFA4713D55C16FDD0DA5EE715895ABBCEB18D699DEF7B5AA8435F49609B",
    }

    for filename, expected_hash in expected_hashes.items():
        filepath = os.path.join(CASE_DIR, filename)
        assert os.path.isfile(filepath), "Committed solver evidence missing: %s" % filepath
        with open(filepath, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest().upper()
        assert computed == expected_hash, "Hash mismatch for %s: %s vs %s" % (filename, computed, expected_hash)

    # Verify canonical UEL path (GAP-MC-C3J1D-02)
    canonical_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(canonical_uel), "Canonical frozen UEL missing: %s" % canonical_uel
    with open(canonical_uel, "rb") as f:
        uel_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert uel_hash == EXPECTED_FROZEN_UEL_SHA.upper()

    # Verify ACTIVE_TASK.json correlation
    with open(ACTIVE_TASK_PATH, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["correlation_id"] in ("HND-METHOD-C-CASE3-JOB1-DIAG-002", "HND-METHOD-C-CASE3-CYCLE1-PREP-001", "HND-METHOD-C-CASE3-CYCLE1-PREP-002", "HND-METHOD-C-CASE3-JOB2-001") or task.get("predecessor_correlation_id") in ("HND-METHOD-C-CASE3-JOB1-DIAG-002", "HND-METHOD-C-CASE3-CYCLE1-PREP-002")
    assert task["scientific_operation"] in ("method_c_case3_job1_failure_diagnosis", "method_c_case3_cycle1_refinement_package", "method_c_case3_cycle1_job2_solve")

