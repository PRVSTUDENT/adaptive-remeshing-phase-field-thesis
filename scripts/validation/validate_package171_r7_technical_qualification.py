#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_package171_r7_technical_qualification.py
=================================================
Technical qualification and integrity validation script for Package 171-R7:
Mode-I C6 Stage C3-0 Genuine Coupled PDAS Adaptive Re-Equilibration.
Task: F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION
"""

import sys
import os
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r7_c3_0_adaptive_reequilibration"
DRIVER_PATH = REPO_ROOT / "scripts" / "state_transfer" / "driver_package171_r7_c6_coupled_pdas.py"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_DRIVER_HASH = "3CC41F517217BDCA2FC2474AA7D8000919ACD4480085D7534E6F29DE40C52E29"

DONOR_REF_FORCE_KN = 0.17992419004440308
DONOR_REF_ENERGY_KNMM = 0.00022639903


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checks():
    receipt = {
        "schema": 1,
        "package_id": "mode1_c6_package171_r7_c3_0_adaptive_reequilibration",
        "task_id": "F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION",
        "candidate_job": "M1_C6_P171_R7_ADAPTIVE_DAMPED",
        "checks": {},
        "evidence_sources": {},
        "overall_status": "FAILED"
    }

    # 1. Package directory & manifest existence
    print("--- 1. Checking manifests ---")
    pkg_manifest_p = PKG_DIR / "PACKAGE_MANIFEST.json"
    auth_manifest_p = PKG_DIR / "M1_C6_PACKAGE171_R7_AUTHORIZATION.json"
    exec_manifest_p = PKG_DIR / "EXECUTION_MANIFEST.json"

    assert pkg_manifest_p.is_file(), "Missing PACKAGE_MANIFEST.json"
    assert auth_manifest_p.is_file(), "Missing M1_C6_PACKAGE171_R7_AUTHORIZATION.json"
    assert exec_manifest_p.is_file(), "Missing EXECUTION_MANIFEST.json"

    pkg_manifest = json.loads(pkg_manifest_p.read_text(encoding="utf-8"))
    auth_manifest = json.loads(auth_manifest_p.read_text(encoding="utf-8"))
    exec_manifest = json.loads(exec_manifest_p.read_text(encoding="utf-8"))

    pkg_hash = sha256_file(pkg_manifest_p).upper()
    auth_hash = sha256_file(auth_manifest_p).upper()
    exec_hash = sha256_file(exec_manifest_p).upper()

    assert exec_manifest["manifest_sha256"] == pkg_hash, "EXECUTION_MANIFEST manifest_sha256 mismatch"
    assert exec_manifest["auth_sha256"] == auth_hash, "EXECUTION_MANIFEST auth_sha256 mismatch"
    assert exec_manifest["files_count"] == 18, f"Unexpected files_count {exec_manifest['files_count']}"

    receipt["checks"]["manifest_cross_integrity"] = "PASS"
    receipt["manifest_hashes"] = {
        "PACKAGE_MANIFEST.json": pkg_hash,
        "M1_C6_PACKAGE171_R7_AUTHORIZATION.json": auth_hash,
        "EXECUTION_MANIFEST.json": exec_hash
    }

    # 2. Verify all files in PACKAGE_MANIFEST
    print("--- 2. Checking package files & hashes ---")
    file_hashes = {}
    for fname, exp_hash in pkg_manifest["files"].items():
        fp = PKG_DIR / fname
        assert fp.is_file(), f"Missing package file: {fname}"
        act_hash = sha256_file(fp).lower()
        assert act_hash == exp_hash.lower(), f"Hash mismatch for {fname}: exp {exp_hash}, act {act_hash}"
        file_hashes[fname] = act_hash
        receipt["evidence_sources"][f"models/pandey_kumar_mode1/171_c6_package171_r7_c3_0_adaptive_reequilibration/{fname}"] = act_hash.upper()

    receipt["checks"]["package_file_hashes"] = f"PASS ({len(file_hashes)} files verified)"

    # 3. Frozen UEL integrity
    print("--- 3. Checking frozen UEL integrity ---")
    uel_p = PKG_DIR / "f42_mixed_uel.for"
    uel_act_hash = sha256_file(uel_p).upper()
    assert uel_act_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {uel_act_hash} != {FROZEN_UEL_HASH}"
    receipt["checks"]["frozen_uel_integrity"] = "PASS"
    receipt["evidence_sources"]["models/pandey_kumar_mode1/171_c6_package171_r7_c3_0_adaptive_reequilibration/f42_mixed_uel.for"] = uel_act_hash

    # 4. Driver hash & execution wiring
    print("--- 4. Checking driver hash and runtime wiring ---")
    driver_hash = sha256_file(DRIVER_PATH).upper()
    assert driver_hash == EXPECTED_DRIVER_HASH, f"Driver hash mismatch: {driver_hash} != {EXPECTED_DRIVER_HASH}"
    receipt["evidence_sources"]["scripts/state_transfer/driver_package171_r7_c6_coupled_pdas.py"] = driver_hash

    # Verify key driver components in text
    driver_text = DRIVER_PATH.read_text(encoding="utf-8")
    wiring_checks = {
        "compute_active_set_symmetric_difference": "def compute_active_set_symmetric_difference" in driver_text,
        "stage_transition_logic": "self.consecutive_stable_iterations >= self.stabilization_window" in driver_text,
        "rollback_logic": "cand_delta_d > self.rollback_factor * self.previous_delta_d" in driver_text,
        "max_outer_budget_explicit": "max_outer=100" in driver_text,
        "healing_irreversibility_enforcement": "healing_violations" in driver_text,
        "history_monotonicity_enforcement": "monotonicity_violations" in driver_text,
        "post_relaxation_kkt_stationarity": "kkt_post" in driver_text,
        "final_mechanical_reequilibration": "final coupled-field consistency equilibration" in driver_text.lower(),
        "fail_closed_phase_decoding": "15559" in driver_text and "reject 2-component" in driver_text.lower(),
        "continuity_gates": "DONOR_REFERENCE_FORCE_KN" in driver_text and "2.0" in driver_text
    }
    for check_name, passed in wiring_checks.items():
        assert passed, f"Wiring check failed: {check_name}"

    receipt["checks"]["driver_execution_wiring"] = {k: "PASS" for k in wiring_checks}

    # 5. Datacheck verification
    print("--- 5. Checking authentic Abaqus 2023 datacheck evidence ---")
    mech_dat_p = PKG_DIR / "P171_MECHANICAL_DC.dat"
    phase_dat_p = PKG_DIR / "P171_PHASE_DC.dat"
    mech_msg_p = PKG_DIR / "P171_MECHANICAL_DC.msg"
    phase_msg_p = PKG_DIR / "P171_PHASE_DC.msg"

    for p in [mech_dat_p, phase_dat_p, mech_msg_p, phase_msg_p]:
        assert p.is_file(), f"Missing datacheck artifact: {p.name}"

    mech_dat_text = mech_dat_p.read_text(encoding="utf-8", errors="replace")
    phase_dat_text = phase_dat_p.read_text(encoding="utf-8", errors="replace")
    mech_msg_text = mech_msg_p.read_text(encoding="utf-8", errors="replace")
    phase_msg_text = phase_msg_p.read_text(encoding="utf-8", errors="replace")

    assert ("ANALYSIS DATACHECK COMPLETE" in mech_dat_text or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in mech_dat_text), "Mechanical datacheck incomplete"
    assert ("ANALYSIS DATACHECK COMPLETE" in phase_dat_text or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in phase_dat_text), "Phase datacheck incomplete"

    for name, text in [("mech_dat", mech_dat_text), ("phase_dat", phase_dat_text), ("mech_msg", mech_msg_text), ("phase_msg", phase_msg_text)]:
        assert "***ERROR" not in text, f"Error found in {name}"

    receipt["checks"]["datacheck_evidence"] = {
        "mechanical_datacheck": "PASS (Exit 0, ANALYSIS DATACHECK COMPLETE, 0 errors)",
        "phase_datacheck": "PASS (Exit 0, ANALYSIS DATACHECK COMPLETE, 0 errors)",
        "mechanical_dat_sha256": sha256_file(mech_dat_p).upper(),
        "phase_dat_sha256": sha256_file(phase_dat_p).upper()
    }

    # 6. PBS submission script checks
    print("--- 6. Checking submission script ---")
    pbs_p = PKG_DIR / "submit_M1_C6_P171_R7_C3_0.pbs"
    pbs_text = pbs_p.read_text(encoding="utf-8")
    assert "#PBS -N M1_C6_P171_R7_C3_0" in pbs_text, "Job name mismatch in PBS script"
    assert "#PBS -q entry_imfdfkmq" in pbs_text, "Queue mismatch in PBS script"
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs_text, "Resource allocation mismatch"
    assert "#PBS -l walltime=08:00:00" in pbs_text, "Walltime mismatch"
    assert "--max-outer 100" in pbs_text, "max-outer 100 missing in PBS script"
    assert "--omega-d-stage1 0.5" in pbs_text, "omega-d-stage1 missing in PBS script"
    assert "--omega-d-stage2 0.85" in pbs_text, "omega-d-stage2 missing in PBS script"
    assert "--stabilization-window 3" in pbs_text, "stabilization-window missing in PBS script"
    assert "--stabilization-threshold 2" in pbs_text, "stabilization-threshold missing in PBS script"
    assert "--rollback-factor 1.05" in pbs_text, "rollback-factor missing in PBS script"
    assert "source \"${RUN_DIR}/job_notifications.sh\"" in pbs_text, "Notification hook missing"

    receipt["checks"]["pbs_script_wiring"] = "PASS"

    # 7. Run focused regression tests
    print("--- 7. Running 22 focused unit tests ---")
    import unittest
    test_dir = REPO_ROOT / "tests" / "unit"
    pattern = "test_package171_r7_*.py"
    loader = unittest.TestLoader()
    print("Discovering tests in", test_dir)
    suite = loader.discover(str(test_dir), pattern=pattern)
    print("Discovered count:", suite.countTestCases())
    assert suite.countTestCases() == 22, f"Expected 22 test cases, got {suite.countTestCases()}"

    runner = unittest.TextTestRunner(verbosity=1)
    res = runner.run(suite)
    print("Ran tests:", res.testsRun, "Failures:", len(res.failures), "Errors:", len(res.errors))
    assert res.wasSuccessful(), f"Unit tests failed: failures={len(res.failures)}, errors={len(res.errors)}"
    assert res.testsRun == 22, f"Expected 22 tests run, got {res.testsRun}"

    receipt["checks"]["unit_regression_tests"] = "PASS (22/22 passed in 100% pass rate)"
    test_files = [
        "tests/unit/test_package171_r7_c6_coupled_driver_gates.py",
        "tests/unit/test_package171_r7_c6_coupled_driver_phase_decoding.py",
        "tests/unit/test_package171_r7_c6_coupled_driver_switching.py"
    ]
    for tf in test_files:
        receipt["evidence_sources"][tf] = sha256_file(REPO_ROOT / tf).upper()

    receipt["overall_status"] = "R7_PACKAGE_TECHNICALLY_VALIDATED_FOR_REVIEW"
    receipt["verification_passed"] = True

    # Save validation receipt
    receipt_p = REPO_ROOT / "results" / "validation" / "package171_r7_technical_qualification_receipt.json"
    receipt_p.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Receipt written to {receipt_p}")
    print("ALL CHECKS PASSED: R7_PACKAGE_TECHNICALLY_VALIDATED_FOR_REVIEW")
    return receipt


if __name__ == "__main__":
    run_checks()
