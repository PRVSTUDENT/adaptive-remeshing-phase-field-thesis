#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_same_mesh_control_staging.py
=================================
Unit and regression test suite verifying the paired same-mesh control experiment
staging and authentic datacheck qualification under Task F1622.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG172_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "172_c5_same_mesh_old_control"
PKG173_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "173_c5_same_mesh_corrected_control"
RECEIPT_PATH = REPO_ROOT / "results" / "validation" / "same_mesh_control_datacheck_receipt.json"
REPORT_PATH = REPO_ROOT / "results" / "validation" / "same_mesh_control_staging_report.md"
TASK_DEF_PATH = REPO_ROOT / "project_coordination" / "task_definitions" / "F1622-METHOD-C-SAME-MESH-ABAQUS-CONTROL-STAGING.json"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_frozen_uel_integrity():
    for pkg_dir in [PKG172_DIR, PKG173_DIR]:
        uel_p = pkg_dir / "f42_mixed_uel.for"
        assert uel_p.is_file(), f"f42_mixed_uel.for missing in {pkg_dir.name}"
        assert sha256_file(uel_p) == FROZEN_UEL_HASH, f"UEL hash mismatch in {pkg_dir.name}"


def test_package_structure_and_files():
    required_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_same_mesh_control_pdas.py",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "PACKAGE_MANIFEST.json",
        "run_datacheck.sh",
        "smoke_import.py"
    ]
    for fn in required_files:
        assert (PKG172_DIR / fn).is_file(), f"Missing {fn} in Package 172"
        assert (PKG173_DIR / fn).is_file(), f"Missing {fn} in Package 173"


def test_identical_nodal_and_boundary_assets():
    shared_files = [
        "active_set_boundary_cards.inc",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "job_notifications.sh"
    ]
    for fn in shared_files:
        hash_172 = sha256_file(PKG172_DIR / fn)
        hash_173 = sha256_file(PKG173_DIR / fn)
        assert hash_172 == hash_173, f"Shared asset {fn} differs between Package 172 and 173"


def test_manifest_verification_and_anderson_disabled():
    with open(PKG172_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m172 = json.load(f)
    with open(PKG173_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m173 = json.load(f)

    # Anderson disabled in both arms
    assert m172["numerical_parameters"]["anderson_enabled"] is False
    assert m173["numerical_parameters"]["anderson_enabled"] is False

    # Identical numerical solver settings
    for key in ["damping_omega_d_stage1", "damping_omega_d_stage2", "damping_omega_u_stage1", "damping_omega_u_stage2",
                "max_active_cardinality", "max_symmetric_diff", "max_added_nodes", "stabilization_window",
                "rollback_factor", "divergence_factor", "catastrophic_delta_d_cap", "max_outer_iterations",
                "delta_d_tol", "delta_u_tol_mm", "delta_h_tol_MPa", "kkt_tol"]:
        assert m172["numerical_parameters"][key] == m173["numerical_parameters"][key], f"Mismatch in {key}"

    # Receiver mesh identical
    assert m172["receiver_mesh"]["elements_quad"] == 12996
    assert m173["receiver_mesh"]["elements_quad"] == 12996
    assert m172["receiver_mesh"]["physical_nodes"] == 13278
    assert m173["receiver_mesh"]["physical_nodes"] == 13278


def test_arm1_history_perturbation():
    with open(PKG172_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m172 = json.load(f)
    peak_err = m172["transfer_operator"]["history_perturbation_peak_MPa"]
    rms_err = m172["transfer_operator"]["history_perturbation_rms_MPa"]
    assert abs(peak_err - 6.3491) < 0.01, f"Expected ~6.3491 MPa peak perturbation, got {peak_err}"
    assert abs(rms_err - 0.0681) < 0.01, f"Expected ~0.0681 MPa RMS perturbation, got {rms_err}"


def test_arm2_history_identity():
    with open(PKG173_DIR / "PACKAGE_MANIFEST.json", "r", encoding="utf-8") as f:
        m173 = json.load(f)
    peak_err = m173["transfer_operator"]["history_perturbation_peak_MPa"]
    rms_err = m173["transfer_operator"]["history_perturbation_rms_MPa"]
    assert peak_err <= 1.0e-12, f"Expected machine identity (<= 1e-12 MPa), got {peak_err}"
    assert rms_err <= 1.0e-14, f"Expected machine identity RMS (<= 1e-14 MPa), got {rms_err}"


def test_datacheck_receipt_validity():
    assert RECEIPT_PATH.is_file(), "same_mesh_control_datacheck_receipt.json missing"
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        rec = json.load(f)

    assert rec["task_id"] == "F1622-METHOD-C-SAME-MESH-ABAQUS-CONTROL-STAGING"
    assert rec["status"] == "DATACHECKS_PASSED_BOTH_EXIT_0"
    assert rec["production_pbs_submissions"] == 0
    assert rec["zero_pbs_enforced"] is True
    assert rec["frozen_uel_sha256"] == FROZEN_UEL_HASH

    # Check Arm 1 datachecks
    arm1 = rec["experimental_matrix"]["arm_1_control_old"]
    assert arm1["anderson_enabled"] is False
    assert arm1["mechanical_datacheck"]["exit_code"] == 0
    assert arm1["mechanical_datacheck"]["errors"] == 0
    assert arm1["mechanical_datacheck"]["status"] == "PASS"
    assert arm1["phase_datacheck"]["exit_code"] == 0
    assert arm1["phase_datacheck"]["errors"] == 0
    assert arm1["phase_datacheck"]["status"] == "PASS"

    # Check Arm 2 datachecks
    arm2 = rec["experimental_matrix"]["arm_2_control_corrected"]
    assert arm2["anderson_enabled"] is False
    assert arm2["mechanical_datacheck"]["exit_code"] == 0
    assert arm2["mechanical_datacheck"]["errors"] == 0
    assert arm2["mechanical_datacheck"]["status"] == "PASS"
    assert arm2["phase_datacheck"]["exit_code"] == 0
    assert arm2["phase_datacheck"]["errors"] == 0
    assert arm2["phase_datacheck"]["status"] == "PASS"


def test_dat_files_zero_errors_and_completion_banners():
    dat_files = [
        PKG172_DIR / "P172_MECHANICAL_DC.dat",
        PKG172_DIR / "P172_PHASE_DC.dat",
        PKG173_DIR / "P173_MECHANICAL_DC.dat",
        PKG173_DIR / "P173_PHASE_DC.dat"
    ]
    for df in dat_files:
        assert df.is_file(), f"Missing {df.name}"
        text = df.read_text(encoding="utf-8", errors="replace")
        assert "***ERROR" not in text, f"Error found in {df.name}"
        assert ("THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in text or "ANALYSIS DATACHECK COMPLETE" in text), \
            f"Missing completion banner in {df.name}"


def test_task_definition_conformance():
    assert TASK_DEF_PATH.is_file(), "Task definition missing"
    with open(TASK_DEF_PATH, "r", encoding="utf-8") as f:
        tdef = json.load(f)
    assert tdef["task_id"] == "F1622-METHOD-C-SAME-MESH-ABAQUS-CONTROL-STAGING"
    assert tdef["governance"]["max_new_pbs_submissions"] == 0
    assert tdef["governance"]["zero_pbs_enforced"] is True
