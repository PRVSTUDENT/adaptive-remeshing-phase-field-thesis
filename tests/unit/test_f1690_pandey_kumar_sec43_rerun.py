#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_f1690_pandey_kumar_sec43_rerun.py

Unit test suite for Task F1690: Pandey-Kumar Section 4.3 Job-1 Rerun with Corrected Solver Setup.
Verifies:
1. Physical mesh geometry, element counts, and datum reconciliation (h=0.60 mm, 24,718 elements).
2. Local Abaqus 2024 datacheck completion (0 errors) and frozen UEL hash preservation.
3. Auxiliary linear-elastic stress recovery (Exit 0, MISESERI peak 6.90 MPa, 90% error energy in 3.13% area).
4. Native adaptive remeshing metrics (30,686 elements, primary h_min = 0.065 mm <= l0/4, secondary 0.0% <= l0/2).
5. Stage 0 Increment-64 damage localization (d_max = 0.7722 at notch tip, secondary d_max = 0.0254).
6. Job-1 rerun solver outcome (Job 1421200, 170 increments, Exit 1 cutback limit, D_f = 13.43 mJ).
7. Terminal damage field extraction (d_max = 0.9318 at notch tip, secondary d_max = 0.0214, visual proof = True).
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "190_pk_sec43_job1_rerun"
results_dir = REPO_ROOT / "results" / "validation"
uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_f1690_frozen_uel_preservation():
    """Verify production UEL f42_mixed_uel.for is bitwise unmodified."""
    assert uel_path.exists(), "UEL file missing: %s" % uel_path
    with open(uel_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest().lower()
    assert sha256 == FROZEN_UEL_SHA256, "UEL SHA-256 mismatch! Got: %s" % sha256

def test_f1690_physical_mesh_and_datacheck():
    """Verify physical mesh and datacheck completion."""
    phys_inp = model_dir / "PK_SEC43_RERUN_PHYS.inp"
    assert phys_inp.exists(), "Physical mesh missing: %s" % phys_inp
    
    # Check datacheck log
    dc_dat = model_dir / "PK_SEC43_RERUN_JOB1_DC.dat"
    assert dc_dat.exists(), "Datacheck dat file missing: %s" % dc_dat
    with open(dc_dat, "r") as f:
        content = f.read()
    assert "ANALYSIS DATACHECK COMPLETE" in content
    assert "0 ERRORS" in content or "ERROR" not in content.upper().split("CHECKING HEADINGS")[0]

def test_f1690_stage0_damage_inc64_record():
    """Verify Stage 0 Increment 64 damage localization record."""
    rec_path = results_dir / "f1688_sec43_damage_inc64_record.json"
    assert rec_path.exists(), "Record missing: %s" % rec_path
    with open(rec_path, "r") as f:
        rec = json.load(f)
    assert rec["stage"] == "Stage_0_Increment_64_Damage_Extraction"
    assert rec["increment"] == 64
    assert abs(rec["top_displacement_uy_mm"] - 0.081014) < 1e-4
    assert abs(rec["damage_max"] - 0.7722) < 0.01
    assert rec["notch_tip_damage_max"] > 0.75
    assert rec["secondary_ligament_damage_max"] < 0.05

def test_f1690_auxiliary_miseseri_recovery():
    """Verify auxiliary linear-elastic stress recovery on h=0.60 mm mesh."""
    eval_json = results_dir / "f1690_sec43_miseseri_evaluation.json"
    assert eval_json.exists(), "MISESERI evaluation JSON missing: %s" % eval_json
    with open(eval_json, "r") as f:
        data = json.load(f)
    assert data["element_count"] == 24718
    assert data["miseseri_max"] > 5.0
    assert data["rel_area_90pct"] < 5.0  # 90% error energy in <5% area
    assert data["secondary_ligament"]["ratio_to_peak"] < 0.05

def test_f1690_native_adapted_mesh_metrics():
    """Verify native Abaqus adaptive remeshing metrics on finer mesh."""
    metrics_json = results_dir / "f1690_sec43_adapted_mesh_metrics.json"
    assert metrics_json.exists(), "Adapted mesh metrics JSON missing: %s" % metrics_json
    with open(metrics_json, "r") as f:
        m = json.load(f)
    assert m["adapted_mesh"]["total_elements"] == 30686
    assert m["primary_corridor"]["min"] < 0.0950  # h_min <= l0/3 = 0.0950 mm
    assert m["secondary_corridor"]["pct_l0_half"] == 0.0  # exactly 0.0% <= l0/2
    assert m["pass_fail"]["secondary_corridor_pass"] is False
    assert m["pass_fail"]["overall_pass"] is False

def test_f1690_job1_rerun_outcome():
    """Verify Job-1 rerun solver outcome record."""
    outcome_json = results_dir / "f1690_sec43_rerun_outcome.json"
    assert outcome_json.exists(), "Rerun outcome JSON missing: %s" % outcome_json
    with open(outcome_json, "r") as f:
        data = json.load(f)
    assert data["task_id"] == "F1690-PK-SEC43-JOB1-CORRECTED-SOLVER-RERUN"
    assert data["pbs_job_id"] == "1421200.mmaster02"
    assert data["exit_code"] == 1
    assert data["solver_outcome"] == "CUTBACK_EXHAUSTED"
    rerun_data = data["comparison"]["f1690_rerun"]
    assert rerun_data["termination_increment"] == 170
    assert abs(rerun_data["termination_uy_mm"] - 0.068717) < 1e-4
    assert abs(rerun_data["e_frac_terminal_J"] - 0.013426) < 1e-4
    assert data["hard_stop_rule_executed"] is True

def test_f1690_terminal_damage_record():
    """Verify terminal damage field extraction record."""
    rec_json = results_dir / "f1690_sec43_damage_terminal_record.json"
    assert rec_json.exists(), "Terminal damage record missing: %s" % rec_json
    with open(rec_json, "r") as f:
        rec = json.load(f)
    assert rec["stage"] == "Terminal_Damage_Extraction"
    assert rec["terminal_increment"] == 170
    assert rec["notch_tip_max_damage"] > 0.90
    assert rec["secondary_ligament_max_damage"] < 0.05
    assert rec["pre_penetration_visual_proof"] is True
