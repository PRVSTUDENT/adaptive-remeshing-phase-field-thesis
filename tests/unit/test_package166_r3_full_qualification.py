#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package166_r3_full_qualification.py
Comprehensive qualification and verification suite for Package 166-R3:
1. Restored donor_source schema, authentic C4 Checkpoint 01, target displacement 0.0018603125442191958 mm, and transferred-state provenance.
2. Corrected R2 driver post-phase delta_d calculation preventing false convergence.
3. Non-accumulating history contract H^(k) = max(H0, psi+(u^(k))) and dynamic PDAS.
4. All 14 package file digests verified across PACKAGE_MANIFEST and EXECUTION_MANIFEST.
5. Strict preservation of frozen production UEL SHA-256 (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).
6. Authentic Abaqus 2023 mechanical and phase datachecks status.
7. Real driver initialization without exceptions, verifying nodal/GP array shapes.
8. Execution manifest constraints (1 CPU, <=16 GB RAM, <=8 hours, single-rank serial).
"""

import sys
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.driver_package166_r2_c5_nonaccumulating_history import Package166R2NonAccumulatingDriver

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/166_c5_package166_r3_c2_0_nonaccumulating_history"
PKG_MANIFEST_PATH = PKG_DIR / "PACKAGE_MANIFEST.json"
EXEC_MANIFEST_PATH = PKG_DIR / "EXECUTION_MANIFEST.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_restored_donor_source_and_provenance():
    assert PKG_MANIFEST_PATH.is_file(), "PACKAGE_MANIFEST.json missing"
    manifest = json.loads(PKG_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "donor_source" in manifest, "donor_source schema block missing"
    donor = manifest["donor_source"]
    assert float(donor["target_uy_mm"]) == pytest.approx(0.0018603125442191958, rel=1e-12)
    assert float(donor["c4_max_history_MPa"]) == pytest.approx(6868.951434128797, rel=1e-9)

    ckpt_path = Path(donor["checkpoint"])
    assert ckpt_path.is_file(), f"Donor checkpoint file missing: {ckpt_path}"
    ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
    assert "displacement" in ckpt and "damage" in ckpt and "history" in ckpt, "Invalid donor checkpoint structure"


def test_driver_post_phase_delta_d_gate_logic():
    driver_script = REPO_ROOT / "scripts/state_transfer/driver_package166_r2_c5_nonaccumulating_history.py"
    assert driver_script.is_file(), "Driver script missing"
    content = driver_script.read_text(encoding="utf-8")

    # In driver_package166_c5 (original), delta_d was computed before phase solve (false convergence)
    # In driver_package166_r2_c5, delta_d is computed using post-phase damage vs damage
    assert "delta_d = max(abs(new_damage[n] - damage[n]) for n in new_damage)" in content
    assert "delta_d <= 1e-5" in content


def test_non_accumulating_history_contract():
    manifest = json.loads(PKG_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert "non_accumulating_history_contract" in manifest
    contract = manifest["non_accumulating_history_contract"]
    assert contract["update_rule"] == "H^(k) = max(H0, psi+(u^(k)))"
    assert "H0 = min(H_trans, H_donor_max)" in contract["immutable_baseline"]
    assert "ratcheting_suppression" in contract


def test_all_14_package_digests_and_frozen_uel():
    manifest = json.loads(PKG_MANIFEST_PATH.read_text(encoding="utf-8"))
    exec_manifest = json.loads(EXEC_MANIFEST_PATH.read_text(encoding="utf-8"))

    expected_files = [
        "M1_C5_PACKAGE166_C2_0_REEQUILIBRATION.inp",
        "P166_MECHANICAL_DC.dat",
        "P166_MECHANICAL_DC.inp",
        "P166_PHASE_DC.dat",
        "P166_PHASE_DC.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "run_datacheck.sh",
        "submit_M1_C5_P166_R3_C2_0.pbs"
    ]

    assert len(manifest["file_digests"]) == 14
    for fname in expected_files:
        fpath = PKG_DIR / fname
        assert fpath.is_file(), f"Package file missing: {fname}"
        actual_hash = sha256_file(fpath)
        assert actual_hash == manifest["file_digests"][fname], f"Digest mismatch in PACKAGE_MANIFEST for {fname}"
        assert actual_hash.lower() == exec_manifest["files"][fname].lower(), f"Digest mismatch in EXECUTION_MANIFEST for {fname}"

    # Frozen UEL exact check
    uel_hash = sha256_file(PKG_DIR / "f42_mixed_uel.for")
    assert uel_hash == FROZEN_UEL_SHA256, f"Frozen production UEL hash altered: {uel_hash} != {FROZEN_UEL_SHA256}"


def test_authentic_datachecks_complete():
    mech_dc = PKG_DIR / "P166_MECHANICAL_DC.dat"
    phase_dc = PKG_DIR / "P166_PHASE_DC.dat"

    assert mech_dc.is_file(), "P166_MECHANICAL_DC.dat missing"
    assert phase_dc.is_file(), "P166_PHASE_DC.dat missing"

    mech_text = mech_dc.read_text(encoding="utf-8", errors="ignore")
    phase_text = phase_dc.read_text(encoding="utf-8", errors="ignore")

    assert "ANALYSIS DATACHECK COMPLETE" in mech_text
    assert "ANALYSIS DATACHECK COMPLETE" in phase_text
    assert "ERROR" not in mech_text
    assert "ERROR" not in phase_text


def test_driver_startup_and_dimensions():
    out_dir = REPO_ROOT / "results/validation/tmp_test_r3_qualification"
    extractor = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"

    driver = Package166R2NonAccumulatingDriver(
        package=PKG_DIR,
        output=out_dir,
        extractor=extractor
    )

    driver.load()
    assert driver.target_uy == pytest.approx(0.0018603125442191958, rel=1e-12)
    assert len(driver.d0) == 13278, f"Expected 13278 C5 nodes, got {len(driver.d0)}"
    assert len(driver.u0) == 13278, f"Expected 13278 C5 nodes, got {len(driver.u0)}"
    assert len(driver.h0) == 51984, f"Expected 51984 C5 integration points, got {len(driver.h0)}"


def test_execution_manifest_limits():
    exec_manifest = json.loads(EXEC_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert exec_manifest["batch_name"] == "MODE1_PACKAGE166_R3_M1_C5_P166_R3_C2_0"
    assert len(exec_manifest["jobs"]) == 1
    job = exec_manifest["jobs"][0]

    assert job["cpus"] == 1
    assert job["memory_gb"] <= 16
    assert job["walltime_hours"] <= 8
    assert "single-rank" in job["execution"].lower()
    assert job["max_submissions"] == 1
    assert job["queue"] in ("entry_imfdfkmq", "normal_imfdfkmq")


if __name__ == "__main__":
    test_restored_donor_source_and_provenance()
    test_driver_post_phase_delta_d_gate_logic()
    test_non_accumulating_history_contract()
    test_all_14_package_digests_and_frozen_uel()
    test_authentic_datachecks_complete()
    test_driver_startup_and_dimensions()
    test_execution_manifest_limits()
    print("ALL_QUALIFICATION_TESTS_PASS")
