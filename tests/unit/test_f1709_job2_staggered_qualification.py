# -*- coding: utf-8 -*-
"""
tests/unit/test_f1709_job2_staggered_qualification.py
=====================================================
Unit tests verifying Task F1709 Section 4.3 Job-2 staggered solver qualification:
1. Bitwise preservation of frozen production UEL f42_mixed_uel.for (CE8D5EDC..., 907 lines).
2. Bitwise preservation of standalone staggered variant f42_staggered_variant_uel.for (A0EBB58D..., 918 lines).
3. Integrity of 3-layer production input deck PK_SEC43_JOB2_ADAPTED_PROD.inp (417E749D..., 40,448 lines, 10,065 physical elements).
4. PBS execution script configuration (submit_M1_PK_SEC43_JOB2_STAGGERED.pbs, 1 CPU serial, 16 GB, 8h, dual notifications).
5. Cluster Abaqus 2023 datacheck completion (Exit Code 0, zero errors, matching staged hashes).
6. Authorization manifest validity (F1709_PK_SEC43_JOB2_STAGGERED_AUTHORIZATION.json, max_submissions=1).
7. Forensic failure analysis integrity (f1708_job2_failure_forensic_report.json, node 2238 notch tip divergence).
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_STAGGERED_UEL_SHA = "A0EBB58DDC0309D2AFC2BF45C2EA3B74A8D2ABA5719C05AF1B69B57086AFA633"
EXPECTED_PROD_INP_SHA = "417E749DD934D67C127D1E4B67E9FB32CAAFB384726CCB58169892855907C68B"
EXPECTED_PBS_SHA = "9B0AAA1C218021B95CFEC4F2BADC1AE5C08F268BAABC72763381763784D92125"
EXPECTED_DATACHECK_SHA = "DBFE5590E25D317FE2275F7167214B6684D4A774EF61D53782916A86B801E826"

PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "205_pk_sec43_job2_staggered")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_production_uel_preserved():
    """Verify canonical frozen UEL remains bitwise untouched."""
    canonical_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(canonical_uel), "Canonical f42_mixed_uel.for missing"
    assert sha256_file(canonical_uel) == EXPECTED_FROZEN_UEL_SHA
    with open(canonical_uel, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    assert len(lines) == 907

def test_staggered_variant_uel_integrity():
    """Verify standalone staggered variant UEL integrity and lines."""
    staggered_uel = os.path.join(PKG_DIR, "f42_staggered_variant_uel.for")
    assert os.path.isfile(staggered_uel), "f42_staggered_variant_uel.for missing from Package 205"
    assert sha256_file(staggered_uel) == EXPECTED_STAGGERED_UEL_SHA
    with open(staggered_uel, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    assert len(lines) == 918
    # Confirm key staggered operator split characteristics
    text = "".join(lines)
    assert "f42_staggered_variant_uel.for" in text
    assert "D_VAL = SV_PHASE_COMMITTED(PHYSIDX)" in text
    assert "HIST = SV_H_COMMITTED(PHYSIDX, KPT)" in text
    assert "IF (D_AVG .LT. SV_PHASE_COMMITTED(PHYSIDX)) THEN" in text

def test_job2_production_deck_integrity():
    """Verify Job-2 production deck has exact lines, elements, and SHA-256."""
    prod_inp = os.path.join(PKG_DIR, "PK_SEC43_JOB2_ADAPTED_PROD.inp")
    assert os.path.isfile(prod_inp), "PK_SEC43_JOB2_ADAPTED_PROD.inp missing from Package 205"
    assert sha256_file(prod_inp) == EXPECTED_PROD_INP_SHA
    with open(prod_inp, "r", encoding="latin-1") as f:
        lines = f.readlines()
    assert len(lines) == 40448
    # Confirm two *STATIC, DIRECT steps with cumulative uy = 1.50 mm
    text = "".join(lines)
    assert "*STATIC, DIRECT" in text
    assert "0.0005, 1.0" in text
    assert "0.0002, 0.5" in text
    assert "N_RP, 2, 2, 1.5" in text

def test_job2_pbs_script_configuration():
    """Verify submit_M1_PK_SEC43_JOB2_STAGGERED.pbs matches hash and directives."""
    pbs_file = os.path.join(PKG_DIR, "submit_M1_PK_SEC43_JOB2_STAGGERED.pbs")
    assert os.path.isfile(pbs_file), "submit_M1_PK_SEC43_JOB2_STAGGERED.pbs missing"
    assert sha256_file(pbs_file) == EXPECTED_PBS_SHA
    with open(pbs_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "#PBS -N M1_PK_SEC43_JOB2_STAGGERED" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=08:00:00" in content
    assert 'USER_SUB="f42_staggered_variant_uel.for"' in content
    assert "/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_staggered_f1709" in content
    assert "job_notifications.sh" in content

def test_cluster_datacheck_artifact_verification():
    """Verify cluster Abaqus 2023 datacheck .dat artifact shows zero errors and Exit 0."""
    dat_file = os.path.join(PKG_DIR, "M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.dat")
    assert os.path.isfile(dat_file), "M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.dat missing"
    assert sha256_file(dat_file) == EXPECTED_DATACHECK_SHA
    with open(dat_file, "r", encoding="latin-1") as f:
        content = f.read()
    assert "ANALYSIS DATACHECK COMPLETE" in content
    assert "WITH      9 WARNING MESSAGES ON THE DAT FILE" in content
    assert "ERROR" not in content

def test_authorization_manifest_validity():
    """Verify F1709 authorization manifest has valid schema and matching hashes."""
    manifest_path = os.path.join(PKG_DIR, "F1709_PK_SEC43_JOB2_STAGGERED_AUTHORIZATION.json")
    assert os.path.isfile(manifest_path), "F1709 manifest missing"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["batch_name"] == "MODE1_PK_SEC43_JOB2_STAGGERED"
    assert data["max_submissions"] == 1
    assert data["automatic_retry"] is False
    assert len(data["jobs"]) == 1
    job = data["jobs"][0]
    assert job["id"] == "job2_staggered_prod"
    assert job["cpus"] == 1
    assert job["memory_gb"] == 16
    assert job["walltime_hours"] == 8
    assert job["queue"] == "entry_imfdfkmq"
    # Verify file hashes in manifest
    assert data["files"]["PK_SEC43_JOB2_ADAPTED_PROD.inp"].upper() == EXPECTED_PROD_INP_SHA
    assert data["files"]["f42_staggered_variant_uel.for"].upper() == EXPECTED_STAGGERED_UEL_SHA
    assert data["files"]["f42_mixed_uel.for"].upper() == EXPECTED_FROZEN_UEL_SHA
    assert data["files"]["submit_M1_PK_SEC43_JOB2_STAGGERED.pbs"].upper() == EXPECTED_PBS_SHA
    assert data["files"]["M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.dat"].upper() == EXPECTED_DATACHECK_SHA

def test_forensic_failure_report_accuracy():
    """Verify forensic failure analysis JSON correctly identifies node 2238 notch tip divergence."""
    report_path = os.path.join(REPO_ROOT, "results", "validation", "f1708_job2_failure_forensic_report.json")
    assert os.path.isfile(report_path), "Failure report JSON missing"
    with open(report_path, "r", encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["authentic_pbs_job_id"] == "1421908.mmaster02"
    assert rep["exit_code"] == 1
    assert rep["total_converged_increments"] == 97
    assert rep["terminal_attempted_increment"] == 98
    assert rep["diverging_node_id"] == 2238
    assert rep["diverging_dof"] == 3
    assert rep["divergence_location"] == "initial_notch_tip"
    assert rep["primary_root_cause"] == "FORMULATION_MISMATCH_MONOLITHIC_UEL_WITH_STATIC_DIRECT"
    assert rep["recommended_correction"] == "USE_STANDALONE_STAGGERED_VARIANT_F42_STAGGERED_VARIANT_UEL_FOR"
    assert rep["frozen_production_uel_preserved"] is True

def test_job2_staggered_execution_success():
    """Verify Job-2 staggered execution report confirms Exit 0 across all 4,500 increments with zero cutbacks."""
    rep_path = os.path.join(REPO_ROOT, "results", "validation", "f1709_job2_staggered_execution_report.json")
    assert os.path.isfile(rep_path), "Execution report JSON missing"
    with open(rep_path, "r", encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["pbs_job_id"] == "1421915.mmaster02"
    assert rep["exit_code"] == 0
    assert rep["terminal_status"] == "COMPLETED_EXIT0"
    assert rep["total_increments_solved"] == 4500
    assert rep["total_cutbacks"] == 0
    assert rep["step1_increments"] == 2000
    assert rep["step2_increments"] == 2500
    assert rep["figure16_reproduction_verdict"] == "FULLY_REPRODUCED_AND_NUMERICALLY_VALIDATED"
    assert rep["physical_elements"] == 10065
    assert rep["element_reduction_vs_standard_86k_pct"] == 88.30
    assert rep["measured_speedup_vs_published"] > 2.0

def test_figure16_damage_field_extraction():
    """Verify authentic damage extraction JSON contains all 4 damage states across 10,065 physical elements."""
    json_path = os.path.join(REPO_ROOT, "results", "validation", "f1709_job2_damage_field.json")
    assert os.path.isfile(json_path), "Damage field JSON missing"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["n_phys_elements"] == 10065
    states = data["damage_states"]
    for s in ["state_1_notch_init", "state_2_hole_arrest", "state_3_sec_init", "state_4_severance"]:
        assert s in states, f"Missing state {s}"
        st = states[s]
        assert len(st["elem_damage"]) == 10065
        assert st["max_damage"] >= 0.85

def test_figure16_reproduced_plots_exist():
    """Verify standalone and comparison Figure 16 publication PDF and PNG artifacts exist and are non-empty."""
    fig_dir = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "pandey_kumar_fig14_16_reproduction")
    for fname in ["fig_reproduced_figure16.pdf", "fig_reproduced_figure16.png",
                  "fig_comparison_figure16.pdf", "fig_comparison_figure16.png"]:
        fpath = os.path.join(fig_dir, fname)
        assert os.path.isfile(fpath), f"Figure artifact {fname} missing"
        assert os.path.getsize(fpath) > 100000, f"Figure artifact {fname} unexpectedly small"
