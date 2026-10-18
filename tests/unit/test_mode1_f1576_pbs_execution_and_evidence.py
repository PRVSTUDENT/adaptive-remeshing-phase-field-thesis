"""
Unit and Regression Test Suite for Task F1576:
Recover Running Experiments, Restore Governed PBS Execution, and Advance Method C.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PRODUCTION_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_PROD_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

PACKAGE50_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "50_method_c_experimental_offset_continuation"
)
EVIDENCE_1415036_DIR = os.path.join(PACKAGE50_DIR, "evidence_1415036")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def test_production_uel_remains_frozen():
    assert os.path.exists(PRODUCTION_UEL_PATH), "Production UEL not found"
    actual_hash = sha256_file(PRODUCTION_UEL_PATH)
    assert actual_hash == EXPECTED_PROD_HASH, f"Production UEL modified! {actual_hash} != {EXPECTED_PROD_HASH}"

def test_package50_experimental_uel_hash():
    pkg_uel = os.path.join(PACKAGE50_DIR, "f42_experimental_offset_uel.for")
    assert os.path.exists(pkg_uel), "Package 50 experimental UEL missing"
    assert sha256_file(pkg_uel) == "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"

def test_package50_artifacts_exist():
    expected_files = [
        "M1_EXP_OFFSET_CONT_NOEXTRAP.inp",
        "offset_state_table.csv",
        "submit_M1_EXP_OFFSET_CONT_NOEXTRAP.pbs",
        "PACKAGE_MANIFEST.json",
        "EXPERIMENTAL_OFFSET_CONTINUATION_AUTHORIZATION.json",
    ]
    for fname in expected_files:
        fpath = os.path.join(PACKAGE50_DIR, fname)
        assert os.path.exists(fpath), f"Package 50 missing {fname}"

def test_job_1415036_evidence_and_evaluation():
    eval_path = os.path.join(EVIDENCE_1415036_DIR, "JOB_1415036_EVALUATION.json")
    assert os.path.exists(eval_path), "Evaluation JSON missing"
    with open(eval_path, "r") as f:
        data = json.load(f)

    assert data["pbs_job_id"] == "1415036.mmaster02"
    assert data["exit_code"] == 0
    assert data["status"] == "COMPLETED"
    assert data["exec_host"] == "mnode097/0"
    
    # Check physical solver metrics
    sm = data["solver_metrics"]
    assert sm["step1_iterations"] == 2
    assert abs(sm["step1_rf2_n"] - 5.1365) < 0.01

    assert sm["step2_increments"] == 3
    assert sm["step2_cutbacks"] == 0
    assert sm["predictor_control"] == "extrapolation=NO"
    assert sm["energy_dissipation_monotonic"] is True
    # Fracture dissipation should increase monotonically
    assert sm["step2_inc3_e_fracture_knmm"] > sm["step1_e_fracture_knmm"]

def test_package50_manifest_governance_fields():
    auth_path = os.path.join(PACKAGE50_DIR, "EXPERIMENTAL_OFFSET_CONTINUATION_AUTHORIZATION.json")
    assert os.path.exists(auth_path), "Authorization JSON missing"
    with open(auth_path, "r") as f:
        auth = json.load(f)

    assert auth["adapter"] == "mode1-experimental-offset-v1"
    assert auth["technical_stage"] == "EXPERIMENTAL_OFFSET"
    assert "hypothesis" in auth
    assert auth["jobs"][0]["id"] == "M1_EXP_OFFSET_CONT_NOEXTRAP"
    assert auth["jobs"][0]["cpus"] == 1
    assert auth["jobs"][0]["queue"] == "entry_imfdfkmq"
