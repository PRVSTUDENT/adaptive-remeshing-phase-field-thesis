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
DRIVER_SHA256 = "17C064184A569019E7A2BC72B7880C7F3404B0A9E92C37B2D04F4BE3BAAC7166"
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
    assert task_def["authorized_scope"]["remaining_pbs_submissions"] in (0, 2)
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
    """Verify PACKAGE_MANIFEST.json and Mode-I authorization manifests exist and all file hashes/sizes match on disk."""
    for pkg, cand in [(PKG_174, "M1_C6_R12_PICARD_BASELINE"), (PKG_175, "M1_C6_R12_ANDERSON_M2")]:
        manifest_p = pkg / "PACKAGE_MANIFEST.json"
        assert manifest_p.is_file()
        m = json.loads(manifest_p.read_text(encoding="utf-8"))
        assert m["candidate"] == cand
        assert m["files_count"] == 24
        assert len(m["files"]) == 24

        auth_name = f"{cand}_AUTHORIZATION.json"
        auth_p = pkg / auth_name
        assert auth_p.is_file()
        auth = json.loads(auth_p.read_text(encoding="utf-8"))
        assert auth["max_submissions"] == 1
        assert len(auth["jobs"]) == 1
        assert auth["jobs"][0]["id"] == cand
        assert "PACKAGE_MANIFEST.json" not in auth["files"]

        # Verify every file in *_AUTHORIZATION.json["files"] matches actual on-disk SHA-256
        for fname, expected_lower_sha in auth["files"].items():
            fp = pkg / fname
            assert fp.is_file(), f"Missing auth file {fname} in {pkg.name}"
            assert sha256_file(fp).lower() == expected_lower_sha, f"Auth hash mismatch for {fname} in {pkg.name}"

        # Verify every file in PACKAGE_MANIFEST.json["files"] (including *_AUTHORIZATION.json) matches actual on-disk SHA-256 and size_bytes
        assert auth_name in m["files"], f"{auth_name} missing from PACKAGE_MANIFEST.json in {pkg.name}"
        for fname, entry in m["files"].items():
            fp = pkg / fname
            assert fp.is_file(), f"Missing manifest file {fname} in {pkg.name}"
            assert sha256_file(fp) == entry["sha256"], f"Manifest SHA-256 mismatch for {fname} in {pkg.name}"
            assert fp.stat().st_size == entry["size_bytes"], f"Manifest size_bytes mismatch for {fname} in {pkg.name}"


def test_08_f1630_task_registration_and_daily_error_register():
    """Verify F1630 task definition and 6 November Daily Error Register."""
    f1630_path = REPO_ROOT / "project_coordination" / "task_definitions" / "F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION.json"
    assert f1630_path.is_file()
    f1630 = json.loads(f1630_path.read_text(encoding="utf-8"))
    assert f1630["task_id"] == "F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION"
    assert f1630["predecessor"] == "F1629-METHOD-C-C6-R12-OVERNIGHT-CONTROLLED-PAIR"
    assert f1630["governance"]["driver_sha256"] == DRIVER_SHA256
    assert f1630["governance"]["frozen_uel_sha256"] == FROZEN_UEL_SHA256
    assert len(f1630["authorized_scope"]["named_jobs"]) == 2

    err_reg_path = REPO_ROOT / "project_coordination" / "DAILY_ERROR_REGISTER_2026-11-06.json"
    assert err_reg_path.is_file()
    err_reg = json.loads(err_reg_path.read_text(encoding="utf-8"))
    assert err_reg["total_incidents"] in (2, 3)
    assert err_reg["summary_counts"]["total_distinct_incidents"] in (2, 3)
    assert err_reg["summary_counts"]["independently_verified_resolved_incidents"] in (2, 3)
    assert err_reg["summary_counts"]["unresolved_software_or_metadata_incidents"] == 0
    assert err_reg["summary_counts"]["scientific_validation_dependencies"] == 1
    assert err_reg["summary_counts"]["infrastructure_observability_boundaries"] == 1
    assert len(err_reg["incidents"]) in (2, 3)
    inc1 = err_reg["incidents"][0]
    assert inc1["incident_id"] == "INC-2026-11-06-01"
    assert inc1["incident_status"] == "RESOLVED_VERIFIED"
    assert len(inc1["code_defects"]) == 4
    assert all(d["status"] == "RESOLVED_VERIFIED" for d in inc1["code_defects"])
    inc2 = err_reg["incidents"][1]
    assert inc2["incident_id"] == "INC-2026-11-06-02"
    assert inc2["classification"] == "STALE_AUTHORIZATION_HASH_IN_PACKAGE_MANIFEST"
    assert inc2["incident_status"] == "RESOLVED_VERIFIED"
    if len(err_reg["incidents"]) == 3:
        inc3 = err_reg["incidents"][2]
        assert inc3["incident_id"] == "INC-2026-11-06-03"
        assert inc3["incident_status"] == "RESOLVED_VERIFIED"
    assert "blocked_conditions" in err_reg
    assert len(err_reg["blocked_conditions"]) >= 2


def test_09_evaluator_f1630_contracts_and_matching_iteration_comparison():
    """Verify evaluate_f1629_paired_execution.py validates R12 summary contracts, matching outer iterations, and Anderson activation gating."""
    import tempfile
    from scripts.validation.evaluate_f1629_paired_execution import evaluate

    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        d174 = tmp_path / "pkg174"
        d175 = tmp_path / "pkg175"
        out_dir = tmp_path / "out"
        d174.mkdir()
        d175.mkdir()

        # Case 1: Anderson never activates (gated behind Stage 1 / active-set stabilization)
        telem_stage1 = [
            {
                "outer": 1,
                "stage": 1,
                "anderson_accelerated": False,
                "anderson_applied": False,
                "pdas_active_count": 15559,
                "pdas_free_count": 0,
                "active_set_symmetric_diff": None,
                "added_nodes_count": None,
                "removed_nodes_count": None,
                "attempted_transition": False,
                "transition_activated": False,
                "rollback_triggered": False,
                "delta_d": 0.145,
                "raw_delta_d": 0.290,
                "delta_u_relaxed": None,
                "delta_u_raw": None,
                "delta_h": 14.047,
                "raw_healing_min": 0.0,
                "raw_healing_violations": 0,
                "free_error": 0.0,
                "dual_error": 0.0,
                "complementarity": 0.0,
                "kkt_post_passed": True,
            },
            {
                "outer": 2,
                "stage": 1,
                "anderson_accelerated": False,
                "anderson_applied": False,
                "pdas_active_count": 14451,
                "pdas_free_count": 1108,
                "active_set_symmetric_diff": 1108,
                "added_nodes_count": 0,
                "removed_nodes_count": 1108,
                "attempted_transition": False,
                "transition_activated": False,
                "rollback_triggered": False,
                "delta_d": 0.0726,
                "raw_delta_d": 0.1452,
                "delta_u_relaxed": 5.33e-6,
                "delta_u_raw": 5.33e-6,
                "delta_h": 3.55,
                "raw_healing_min": -1.4e-8,
                "raw_healing_violations": 0,
                "free_error": 1.2e-8,
                "dual_error": 2.0e-8,
                "complementarity": 9.5e-10,
                "kkt_post_passed": True,
            },
        ]
        nonconv_summary = {
            "status": "NONCONVERGED",
            "stage": 1,
            "outer_iterations_completed": 2,
            "anderson_accelerations_count": 0,
            "anderson_fallbacks_count": 0,
            "anderson_resets_count": 0,
        }
        (d174 / "live_iteration_telemetry.json").write_text(json.dumps(telem_stage1), encoding="utf-8")
        (d175 / "live_iteration_telemetry.json").write_text(json.dumps(telem_stage1), encoding="utf-8")
        (d174 / "re_equilibration_summary.json").write_text(json.dumps(nonconv_summary), encoding="utf-8")
        (d175 / "re_equilibration_summary.json").write_text(json.dumps(nonconv_summary), encoding="utf-8")

        res1 = evaluate(
            d174,
            d175,
            job_174="1420429.mmaster02",
            job_175="1420430.mmaster02",
            out_dir=out_dir,
            task_id="F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION",
            output_prefix="f1630_test1",
        )
        assert res1["comparison"]["anderson_effect_classification"] == "ANDERSON_NEVER_ACTIVATED_GATED_BY_STAGE1_ACTIVE_SET"
        assert res1["comparison"]["demonstrated_anderson_effect"] is False
        assert res1["comparison"]["matching_iterations"]["common_iterations_count"] == 2
        assert res1["comparison"]["matching_iterations"]["identical_across_all_common_iterations"] is True

        # Case 2: R12 lowercase summary contract (reaction_force_kn, total_energy_knmm) and Anderson convergence
        telem_conv_b = [
            telem_stage1[0],
            {
                **telem_stage1[1],
                "stage": 2,
                "anderson_accelerated": True,
                "anderson_applied": True,
                "pdas_active_count": 120,
                "pdas_free_count": 15439,
                "active_set_symmetric_diff": 0,
                "added_nodes_count": 0,
                "removed_nodes_count": 0,
                "transition_activated": True,
                "delta_d": 5.0e-6,
                "raw_delta_d": 8.0e-6,
                "delta_u_relaxed": 5.0e-10,
                "delta_u_raw": 5.0e-10,
                "delta_h": 5.0e-5,
                "kkt_post_passed": True,
            },
        ]
        conv_summary_b = {
            "status": "CONVERGED",
            "stage": 2,
            "outer_iterations_completed": 2,
            "reaction_force_kn": 0.17992419,
            "total_energy_knmm": 0.00022639903,
            "healing_violations_count": 0,
            "history_monotonicity": True,
            "thermodynamic_consistency": True,
            "coupled_field_consistency_u_pass": True,
            "coupled_field_consistency_h_pass": True,
            "anderson_accelerations_count": 1,
            "anderson_fallbacks_count": 0,
            "anderson_resets_count": 0,
        }
        (d175 / "live_iteration_telemetry.json").write_text(json.dumps(telem_conv_b), encoding="utf-8")
        (d175 / "re_equilibration_summary.json").write_text(json.dumps(conv_summary_b), encoding="utf-8")

        res2 = evaluate(
            d174,
            d175,
            job_174="1420429.mmaster02",
            job_175="1420430.mmaster02",
            out_dir=out_dir,
            task_id="F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION",
            output_prefix="f1630_test2",
        )
        assert res2["arm_b_anderson"]["gates"]["overall_physical_acceptance_pass"] is True
        assert res2["comparison"]["anderson_effect_classification"] == "ANDERSON_ACTIVATED_DECISIVE_CONVERGENCE"
        assert res2["comparison"]["demonstrated_anderson_effect"] is True
        assert res2["comparison"]["matching_iterations"]["first_divergence_outer"] == 2


