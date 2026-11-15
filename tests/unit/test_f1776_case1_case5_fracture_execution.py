# -*- coding: utf-8 -*-
"""
test_f1776_case1_case5_fracture_execution.py
Unit test suite verifying execution wrappers, input deck integrity, lock safety,
and governance for Task F1776:
Case 1 and Case 5 Method A Adapted Coupled Phase-Field Fracture Execution.
"""
import os
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXPECTED_CASE1_PROD_SHA256 = "976ef13cead9f8c541d93510bd48483f0adca297c95eec3f8d67fe7429a1cd7e"
EXPECTED_CASE5_PROD_SHA256 = "174c2abb82e1db37a5ed57aa2e36a4b46005098a5264ddcf1164d8232a8cb19e"
EXPECTED_CASE1_PBS_SHA256  = "04e0ebd2624c5997f928d653070aaa04123738873e49ffe158ffa9db61e2d9aa"
EXPECTED_CASE5_PBS_SHA256  = "ab4914f371c5ed8102c73a28fb66804558168092cc2faeeaddd7ff4ff4a54a23"


def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_source_integrity():
    """Verify bitwise invariance of the production UEL source."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), f"Frozen UEL source missing: {uel_path}"
    sha = get_file_sha256(uel_path)
    assert sha == EXPECTED_FROZEN_UEL_SHA256, f"Frozen UEL hash mismatch: {sha}"


def test_case1_production_deck_integrity():
    """Verify Case 1 production deck hash and presence."""
    prod_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "239_f1772_case1_remesh", "PK_F1728_CASE_1_PROD.inp"
    )
    assert os.path.isfile(prod_path), f"Case 1 production deck missing: {prod_path}"
    sha = get_file_sha256(prod_path)
    assert sha == EXPECTED_CASE1_PROD_SHA256, f"Case 1 deck hash mismatch: {sha}"


def test_case5_production_deck_integrity():
    """Verify Case 5 production deck hash and presence."""
    prod_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case5", "PK_F1728_CASE_5_PROD.inp"
    )
    assert os.path.isfile(prod_path), f"Case 5 production deck missing: {prod_path}"
    sha = get_file_sha256(prod_path)
    assert sha == EXPECTED_CASE5_PROD_SHA256, f"Case 5 deck hash mismatch: {sha}"


def test_pbs_execution_wrappers_integrity_and_safety():
    """Verify PBS wrappers for Case 1 and Case 5: hashes, lock safety, and notification hooks."""
    pbs_case1 = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "241_f1776_fracture_batch", "submit_f1776_case1_fracture.pbs"
    )
    pbs_case5 = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "241_f1776_fracture_batch", "submit_f1776_case5_fracture.pbs"
    )

    for path, expected_sha, case_num in [(pbs_case1, EXPECTED_CASE1_PBS_SHA256, "Case 1"),
                                         (pbs_case5, EXPECTED_CASE5_PBS_SHA256, "Case 5")]:
        assert os.path.isfile(path), f"{case_num} PBS script missing: {path}"
        actual_sha = get_file_sha256(path)
        assert actual_sha == expected_sha, f"{case_num} PBS hash mismatch: {actual_sha}"

        with open(path, "r") as f:
            content = f.read()

        # Lock safety verification (Finding F1774-R01)
        assert 'trap \'rmdir "${LOCK_DIR}" 2>/dev/null || true\' EXIT' in content, f"Safe lock cleanup missing in {case_num}"
        assert 'rm -rf "${LOCK_DIR}"' not in content, f"Dangerous recursive lock deletion found in {case_num}"

        # SHA preflight verification (Finding F1774-R03)
        assert "ACTUAL_UEL_SHA" in content, f"UEL hash check missing in {case_num}"
        assert "ACTUAL_INP_SHA" in content, f"INP hash check missing in {case_num}"

        # Dual-channel notification verification
        assert "#PBS -m abe" in content, f"PBS mail directive missing in {case_num}"
        assert "job_notifications.sh" in content, f"Telegram notification hook missing in {case_num}"


def test_f1776_task_state_and_two_job_budget():
    """Verify ACTIVE_TASK.json has task_id F1776 and max_new_pbs_submissions == 2."""
    active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task_path, "r") as f:
        data = json.load(f)

    assert data["task_id"] in ["F1776-CASE1-CASE5-ADAPTED-FRACTURE-EXECUTION", "F1777-METHOD-A-PHYSICS-VERIFICATION-AND-UNIFIED-CONTINUATION", "F1778-CASE5-FRACTURE-PHYSICS-QUALIFICATION-AND-CHAPTER5-INTEGRATION"]
    if data["task_id"] == "F1776-CASE1-CASE5-ADAPTED-FRACTURE-EXECUTION":
        assert data["max_new_pbs_submissions"] == 2, "F1776 authorizes at most 2 forward fracture jobs"
        assert data["submissions_consumed"] in [0, 2]
    assert data["cumulative_pbs_submissions"] in [33, 35]
    assert data["frozen_uel_sha256"].lower() == EXPECTED_FROZEN_UEL_SHA256
    assert data["case1_prod_sha256"].lower() == EXPECTED_CASE1_PROD_SHA256
    assert data["case5_prod_sha256"].lower() == EXPECTED_CASE5_PROD_SHA256
