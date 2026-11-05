#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_f1629_paired_controlled_execution.py
=========================================
Unit and qualification tests for Task F1629 paired controlled overnight execution
(Arm A: M1_C6_R12_PICARD_BASELINE vs Arm B: M1_C6_R12_ANDERSON_M2).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DRIVER_SHA256 = "282690AB37E8592309B19A6B73BF07758FFEFDF568D6F538267F62A3E93B5B6E"
TASK_DEF_PATH = REPO_ROOT / "project_coordination" / "task_definitions" / "F1629-METHOD-C-C6-R12-OVERNIGHT-CONTROLLED-PAIR.json"
PKG_174 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "174_c6_r12_picard_baseline"
PKG_175 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "175_c6_r12_anderson_m2"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_01_task_definition_contract():
    """Verify Task F1629 definition integrity, schema, and 2-job authorization."""
    assert TASK_DEF_PATH.is_file(), "Task definition missing"
    task_def = json.loads(TASK_DEF_PATH.read_text(encoding="utf-8"))
    assert task_def["task_id"] == "F1629-METHOD-C-C6-R12-OVERNIGHT-CONTROLLED-PAIR"
    assert task_def["authorized_scope"]["max_new_pbs_submissions"] == 2
    assert task_def["authorized_scope"]["remaining_pbs_submissions"] == 2
    assert len(task_def["authorized_scope"]["named_jobs"]) == 2
    cands = [j["candidate"] for j in task_def["authorized_scope"]["named_jobs"]]
    assert "M1_C6_R12_PICARD_BASELINE" in cands
    assert "M1_C6_R12_ANDERSON_M2" in cands


def test_02_production_uel_bitwise_integrity():
    """Verify production UEL f42_mixed_uel.for in both packages bitwise matches frozen standard."""
    for pkg in [PKG_174, PKG_175]:
        uel_path = pkg / "f42_mixed_uel.for"
        assert uel_path.is_file(), f"Missing UEL in {pkg.name}"
        assert sha256_file(uel_path) == FROZEN_UEL_SHA256, f"UEL hash drift in {pkg.name}"


def test_03_driver_source_integrity():
    """Verify driver SHA-256 matches registered hash."""
    driver_path = REPO_ROOT / "scripts" / "state_transfer" / "driver_package171_r12_c6_coupled_pdas.py"
    assert driver_path.is_file()
    assert sha256_file(driver_path) == DRIVER_SHA256


def test_04_mesh_and_transfer_state_identity():
    """Verify transferred states (u, d, H, bounds, BCs) are bitwise identical between Pkg 174 and 175."""
    check_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "initial_conditions_solution.inc",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "M1_C6_PACKAGE171_R12_C3_0_ADAPTIVE_REEQUILIBRATION.inp",
        "P171_ITER1_MECH.inp",
        "P171_ITER1_PHASE.inp",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
    ]
    for fn in check_files:
        p174 = PKG_174 / fn
        p175 = PKG_175 / fn
        assert p174.is_file(), f"Missing {fn} in Pkg 174"
        assert p175.is_file(), f"Missing {fn} in Pkg 175"
        assert sha256_file(p174) == sha256_file(p175), f"State mismatch in {fn} between Pkg 174 and 175!"


def test_05_pbs_submission_scripts_paired_difference():
    """Verify that the ONLY intended numerical difference between PBS scripts is Anderson acceleration."""
    pbs_174 = (PKG_174 / "submit_M1_C6_R12_PICARD_BASELINE.pbs").read_text(encoding="utf-8")
    pbs_175 = (PKG_175 / "submit_M1_C6_R12_ANDERSON_M2.pbs").read_text(encoding="utf-8")

    # Both must use entry_imfdfkmq, 1 CPU, 16gb, 8h
    for pbs in [pbs_174, pbs_175]:
        assert "#PBS -q entry_imfdfkmq" in pbs
        assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs
        assert "#PBS -l walltime=08:00:00" in pbs
        assert "--max-outer 140" in pbs
        assert "--omega-d-stage1 0.50" in pbs
        assert "--omega-d-stage2 0.85" in pbs
        assert "--omega-u-stage1 1.00" in pbs
        assert "--omega-u-stage2 0.85" in pbs

    # Pkg 174 has --no-anderson
    assert "--no-anderson" in pbs_174
    assert "--enable-anderson" not in pbs_174
    assert "M1_C6_R12_PICARD_BASELINE" in pbs_174

    # Pkg 175 has --enable-anderson and specific params
    assert "--enable-anderson" in pbs_175
    assert "--no-anderson" not in pbs_175
    assert "--anderson-memory 2" in pbs_175
    assert "--anderson-beta 0.85" in pbs_175
    assert "--anderson-reg 1e-6" in pbs_175
    assert "--anderson-gamma-max 200.0" in pbs_175
    assert "--anderson-max-step-cap 0.045" in pbs_175
    assert "M1_C6_R12_ANDERSON_M2" in pbs_175


def test_06_driver_cli_parsing_regression():
    """Verify CLI parser for both baseline and anderson modes."""
    from scripts.state_transfer.driver_package171_r12_c6_coupled_pdas import build_argument_parser

    parser = build_argument_parser()

    # Parse baseline args
    args_base = parser.parse_args([
        "--package", str(PKG_174),
        "--output", "test_out_base",
        "--extractor", "scripts/validation/extract_package148_iteration.py",
        "--no-anderson",
    ])
    assert args_base.anderson_enabled is False

    # Parse anderson args
    args_and = parser.parse_args([
        "--package", str(PKG_175),
        "--output", "test_out_and",
        "--extractor", "scripts/validation/extract_package148_iteration.py",
        "--enable-anderson",
        "--anderson-memory", "2",
        "--anderson-beta", "0.85",
        "--anderson-reg", "1e-6",
        "--anderson-gamma-max", "200.0",
        "--anderson-max-step-cap", "0.045",
    ])
    assert args_and.anderson_enabled is True
    assert args_and.anderson_memory == 2
    assert args_and.anderson_beta == 0.85
    assert args_and.anderson_reg == 1e-6
    assert args_and.anderson_gamma_max == 200.0
    assert args_and.anderson_max_step_cap == 0.045


def test_07_package_manifests_integrity():
    """Verify PACKAGE_MANIFEST.json and Mode-I authorization manifests exist and match."""
    for pkg, cand in [(PKG_174, "M1_C6_R12_PICARD_BASELINE"), (PKG_175, "M1_C6_R12_ANDERSON_M2")]:
        manifest_p = pkg / "PACKAGE_MANIFEST.json"
        assert manifest_p.is_file()
        m = json.loads(manifest_p.read_text(encoding="utf-8"))
        assert m["candidate"] == cand
        assert m["files_count"] >= 20

        auth_p = pkg / f"{cand}_AUTHORIZATION.json"
        assert auth_p.is_file()
        auth = json.loads(auth_p.read_text(encoding="utf-8"))
        assert auth["max_submissions"] == 1
        assert len(auth["jobs"]) == 1
        assert auth["jobs"][0]["id"] == cand
