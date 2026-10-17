#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1547: Package 65 Second Propagation Continuation Execution & Verification.
"""

import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG65_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "65_method_c_propagation_stage2_continuation"
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_frozen_uel_integrity():
    uel_path = PKG65_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "f42_mixed_uel.for missing from Package 65"
    actual_sha = hashlib.sha256(uel_path.read_bytes()).hexdigest().lower()
    assert actual_sha == FROZEN_UEL_SHA, f"Frozen UEL hash mismatch: {actual_sha}"

def test_manifest_structure_and_hashes():
    auth_path = PKG65_DIR / "METHOD_C_PROPAGATION_STAGE2_AUTHORIZATION.json"
    assert auth_path.is_file(), "Authorization manifest missing"
    with open(auth_path, "r", encoding="utf-8") as f:
        auth = json.load(f)
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["batch_name"] == "MODE1_METHOD_C_PROPAGATION_STAGE2"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "C1-2"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    # Check files match on-disk hashes
    for fname, expected_hash in auth["files"].items():
        fpath = PKG65_DIR / fname
        assert fpath.is_file(), f"Manifest file missing on disk: {fname}"
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}: {actual_hash} vs {expected_hash}"

def test_gate6c_transfer_metrics():
    metrics_path = PKG65_DIR / "PROP_STAGE2_TRANSFER_METRICS.json"
    assert metrics_path.is_file(), "Transfer metrics missing"
    with open(metrics_path, "r", encoding="utf-8") as f:
        m = json.load(f)

    # 1. Displacement L2 error <= 1.0%
    assert m["criterion_1_displacement_l2"]["verdict"] == "PASS"
    assert m["criterion_1_displacement_l2"]["value"] <= 1.0

    # 2. Peak damage delta <= 0.02
    assert m["criterion_2_peak_damage"]["verdict"] == "PASS"
    assert m["criterion_2_peak_damage"]["value"] <= 0.02

    # 3. Integrated damage error <= 5.0%
    assert m["criterion_3_integrated_damage"]["verdict"] == "PASS"
    assert m["criterion_3_integrated_damage"]["value"] <= 5.0

    # 4. History non-negativity min(H) >= 0.0
    assert m["criterion_4_history_non_negativity"]["verdict"] == "PASS"
    assert m["criterion_4_history_non_negativity"]["value"] >= 0.0
    assert m["negative_H_count"] == 0

    # 5. Boundary force continuity <= 5.0 N
    assert m["criterion_5_boundary_force_continuity"]["verdict"] == "PASS"
    assert m["criterion_5_boundary_force_continuity"]["value"] <= 5.0

    # 6. Internal energy error <= 0.10%
    assert m["criterion_6_internal_energy"]["verdict"] == "PASS"
    assert m["criterion_6_internal_energy"]["value"] <= 0.10

    # 7. Global energy residual <= 10.0%
    assert m["criterion_7_global_energy_residual"]["verdict"] == "PASS"
    assert m["criterion_7_global_energy_residual"]["value"] <= 10.0

def test_step_definitions_and_schedule():
    inp_path = PKG65_DIR / "M1_MC_PROP_STAGE2_CONT.inp"
    assert inp_path.is_file(), "Input deck missing"
    
    with open(inp_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "*STEP, NAME=Step-1-Equilibrate" in content
    assert "N_RP, 2, 2, 5.5000000000e-03" in content
    assert "*STEP, NAME=Step-2-Continue" in content
    assert "N_RP, 2, 2, 6.0000000000e-03" in content
    assert "*OUTPUT, FIELD, FREQUENCY=5" in content

def test_pbs_submission_script_contract():
    pbs_path = PKG65_DIR / "submit_M1_MC_PROP_STAGE2_CONT.pbs"
    assert pbs_path.is_file(), "PBS script missing"
    text = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -N M1_MC_PROP_S2" in text
    assert "#PBS -q entry_imfdfkmq" in text
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in text
    assert "#PBS -l walltime=04:00:00" in text
    assert "#PBS -m abe" in text
    assert "notification_load_config" in text
    assert "notification_install_terminal_trap" in text
    assert "command -v ifort" in text
    assert "\r" not in text, "CRLF line endings detected in PBS script"

if __name__ == "__main__":
    test_frozen_uel_integrity()
    test_manifest_structure_and_hashes()
    test_gate6c_transfer_metrics()
    test_step_definitions_and_schedule()
    test_pbs_submission_script_contract()
    print("ALL F1547 UNIT TESTS PASSED.")
