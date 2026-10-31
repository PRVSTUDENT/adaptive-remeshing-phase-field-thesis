# -*- coding: utf-8 -*-
"""
test_package150_r2_continuation.py
Unit tests for Package 150 Revision 2 (Package 152) Stage C1-2 forward continuation.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""

import json
import math
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/152_c4_package150_c1_2_continuation_r2"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
R8_EQUIL_SHA256 = "5D627B0340ADB3099D5C8980F733160FFA134787704DEAEBC93D67AB55B8D81C"


def test_package150_r2_directory_and_manifests():
    assert PKG_DIR.is_dir(), "Package 152 directory missing"
    pkg_manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    exec_manifest_path = PKG_DIR / "EXECUTION_MANIFEST.json"
    assert pkg_manifest_path.is_file(), "PACKAGE_MANIFEST.json missing"
    assert exec_manifest_path.is_file(), "EXECUTION_MANIFEST.json missing"

    pkg_manifest = json.loads(pkg_manifest_path.read_text())
    assert pkg_manifest["package_id"] == "PACKAGE_152_C1_2_CONTINUATION_R2"
    assert pkg_manifest["stage"] == "STAGE_C1_2"
    assert pkg_manifest["max_outer"] == 80
    assert pkg_manifest["predecessor_checkpoint_sha256"] == R8_EQUIL_SHA256

    exec_manifest = json.loads(exec_manifest_path.read_text())
    assert exec_manifest["batch_name"] == "MODE1_PACKAGE150_STAGE_C1_2_CONTINUATION_R2"
    assert exec_manifest["adapter"] == "mode1-qualified-batch-v2"
    assert exec_manifest["max_submissions"] == 1
    assert exec_manifest["automatic_retry"] is False
    assert len(exec_manifest["jobs"]) == 1
    job = exec_manifest["jobs"][0]
    assert job["id"] == "M1_C4_P150_C1_2_R2"
    assert job["cpus"] == 1
    assert job["memory_gb"] == 16
    assert job["walltime_hours"] == 8


def test_package150_r2_frozen_uel_integrity():
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "UEL source missing"
    h = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
    assert h == FROZEN_UEL_SHA256, "Production UEL must be 100% bitwise frozen"


def test_package150_r2_pbs_script_and_max_outer():
    pbs_path = PKG_DIR / "submit_M1_C4_P150_C1_2_R2.pbs"
    assert pbs_path.is_file(), "PBS script missing"
    content = pbs_path.read_text()
    assert "#PBS -N M1_C4_P150_C1_2_R2" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=08:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -m abe" in content
    assert "--max-outer 80" in content
    assert "--timeout 25200" in content
    assert "--memory-gb 16" in content


def test_package150_r2_loading_schedule():
    pkg_manifest = json.loads((PKG_DIR / "PACKAGE_MANIFEST.json").read_text())
    sched = pkg_manifest["loading_schedule"]
    assert len(sched["steps"]) == 4
    assert abs(sched["initial_uy_mm"] - 0.001800312544) < 1e-6
    assert abs(sched["target_uy_mm"] - 0.002000) < 1e-6
    for s in sched["steps"]:
        assert s["delta_uy"] <= 5.0e-5 + 1e-9


def test_package150_r2_file_hashes_against_manifest():
    exec_manifest = json.loads((PKG_DIR / "EXECUTION_MANIFEST.json").read_text())
    for fname, expected_hash in exec_manifest["files"].items():
        fpath = PKG_DIR / fname
        assert fpath.is_file(), "Missing package file: %s" % fname
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert actual_hash == expected_hash.lower(), "Hash mismatch for %s" % fname


def test_convergence_horizon_mathematical_justification():
    telemetry_path = REPO_ROOT / "results/validation/package151_convergence_telemetry.json"
    assert telemetry_path.is_file(), "Telemetry file missing"
    telemetry = json.loads(telemetry_path.read_text())
    summary = telemetry["summary_table"]
    assert len(summary) == 30, "Expected 30 outer iterations in authentic telemetry"

    outer30 = summary[-1]
    assert outer30["outer"] == 30
    # delta_u reached 0.031 nm, already below 1.0 nm tolerance
    assert outer30["delta_u_nm"] < 0.05
    # Contraction factor around 0.83-0.85
    rho_h = telemetry["contraction_rates"]["recent_rho_h"]
    assert 0.80 <= rho_h <= 0.88

    # Extrapolated required iterations for delta_h <= 1e-6 MPa:
    current_dh = outer30["delta_h_MPa"]
    target_dh = 1.0e-6
    required_additional = math.ceil(math.log(target_dh / current_dh) / math.log(rho_h))
    projected_total = 30 + required_additional
    assert projected_total <= 80, "max_outer=80 must accommodate projected outer %d" % projected_total
