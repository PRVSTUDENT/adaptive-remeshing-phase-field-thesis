"""Unit test suite for Task F1590: Mode-I Peak Fracture Response, Energy Audit, and Package 60 Smooth-H Transfer."""
import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_PROD_UEL = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
FROZEN_EXP_UEL  = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"

def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().lower()

def test_subroutines_frozen():
    prod_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    assert prod_uel.is_file()
    assert sha256_file(prod_uel) == FROZEN_PROD_UEL

    exp_uel = REPO_ROOT / "models/pandey_kumar_mode1/60_method_c_smooth_h_nonmatching_transfer/f42_experimental_offset_uel.for"
    assert exp_uel.is_file()
    assert sha256_file(exp_uel) == FROZEN_EXP_UEL

def test_package60_manifest_integrity():
    pkg60_dir = REPO_ROOT / "models/pandey_kumar_mode1/60_method_c_smooth_h_nonmatching_transfer"
    manifest_file = pkg60_dir / "PACKAGE_MANIFEST.json"
    auth_file = pkg60_dir / "NONMATCHING_SMOOTH_H_AUTHORIZATION.json"
    assert manifest_file.is_file()
    assert auth_file.is_file()

    with open(manifest_file, "r") as f:
        pkg_manifest = json.load(f)
    with open(auth_file, "r") as f:
        auth_manifest = json.load(f)

    for fname, digest in pkg_manifest["files"].items():
        fpath = pkg60_dir / fname
        assert fpath.is_file(), f"Missing file: {fname}"
        assert sha256_file(fpath) == digest.lower(), f"Hash mismatch: {fname}"

    assert auth_manifest["files"]["PACKAGE_MANIFEST.json"] == sha256_file(manifest_file)

def test_job_1415177_evaluation_metrics():
    eval_file = REPO_ROOT / "models/pandey_kumar_mode1/60_method_c_smooth_h_nonmatching_transfer/evidence_1415177/JOB_1415177_EVALUATION.json"
    assert eval_file.is_file()
    with open(eval_file, "r") as f:
        ev = json.load(f)

    assert ev["pbs_job_id"] == "1415177.mmaster02"
    assert ev["exit_code"] == 0
    assert ev["status"] == "COMPLETED"
    assert ev["zero_increment_reconstruction"]["min_delta_d"] > -0.010, "Healing violation must be strictly > -0.010"
    assert ev["zero_increment_reconstruction"]["healing_reduction_pct"] > 90.0, "Healing reduction must exceed 90%"
    assert ev["acceptance_verdict"] == "PASS"

def test_package48_peak_and_stiffness():
    # Verify Package 48 measured peak values from active solve
    ref_K0 = 137.945520
    ref_Fmax = 757.7785
    ref_u_peak = 0.005857

    pkg48_K0 = 137.842019
    pkg48_Fmax = 732.4603
    pkg48_u_peak = 0.005636

    assert abs((pkg48_K0 - ref_K0) / ref_K0) < 0.001, "K0 must match reference within 0.1%"
    assert abs((pkg48_Fmax - ref_Fmax) / ref_Fmax) < 0.05, "F_max must match reference within 5%"
    assert abs((pkg48_u_peak - ref_u_peak) / ref_u_peak) < 0.05, "u(F_max) must match reference within 5%"
