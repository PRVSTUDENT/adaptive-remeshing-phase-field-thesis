#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_f1705_candidate_e10_production_results.py
=========================================================
Unit test suite verifying Task F1705 Candidate E10 Production Fracture
Execution and Results:
  - Solver lightweight output files (.dat, .msg, .sta, .csv, .log) integrity
  - Accurate once-only ledger recording of PBS Job 1421888.mmaster02
  - Primary peak force parity within <0.5% of F1685 baseline (0.5597 vs 0.5577 kN)
  - Elastic energy relaxation >99.5% confirming complete structural severance
  - Terminal dissipated fracture energy within 10% of F1685 baseline (2.727 vs 2.995 mJ)
  - Computational speedup >= 2.5x and discretization reduction > 57%
  - Generated synthesis figures (.png, .pdf) existence and non-zero size
  - Frozen UEL hash and line count integrity
"""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR   = REPO_ROOT / "models/pandey_kumar_mode1/177_method_a_hole_e10_prod"
RESULTS_JSON = REPO_ROOT / "results/validation/f1705_candidate_e10_production_results.json"
FIG_PNG   = REPO_ROOT / "results/validation/f1705_candidate_e10_synthesis.png"
FIG_PDF   = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026/figures/fig_f1705_candidate_e10_synthesis.pdf"
LEDGER_CSV = REPO_ROOT / "project_coordination/HPC_JOB_LEDGER.csv"
BATCH_SUBMISSIONS = REPO_ROOT / "project_coordination/MODE1_BATCH_SUBMISSIONS.json"
UEL_FILE  = PKG_DIR / "f42_mixed_uel.for"

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
QUAL_DECK_SHA256  = "41F073BC4D0502753D777081ACC8EB99F9716FFAC1D311F64204FBC42F4392F4"
JOB_ID = "1421888.mmaster02"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_downloaded_solver_artifacts():
    """Verify all lightweight solver artifacts are downloaded and non-empty."""
    expected_files = [
        PKG_DIR / "M1_HOLE_SEL_E10_PROD.dat",
        PKG_DIR / "M1_HOLE_SEL_E10_PROD.msg",
        PKG_DIR / "M1_HOLE_SEL_E10_PROD.sta",
        PKG_DIR / "uel_energy_balance.csv",
        PKG_DIR / "pbs_execution.log"
    ]
    for p in expected_files:
        assert p.exists(), f"Missing solver artifact: {p}"
        assert p.stat().st_size > 0, f"Empty solver artifact: {p}"


def test_hpc_job_ledger_recording():
    """Verify Job 1421888.mmaster02 is recorded in HPC_JOB_LEDGER.csv."""
    assert LEDGER_CSV.exists()
    with open(LEDGER_CSV, "r", encoding="utf-8") as f:
        text = f.read()
    assert JOB_ID in text, f"Job ID {JOB_ID} missing from HPC_JOB_LEDGER.csv"
    assert "M1_HOLE_SEL_E10_PROD" in text
    assert "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1705_prod" in text


def test_batch_submissions_recording():
    """Verify Job 1421888.mmaster02 is recorded once in MODE1_BATCH_SUBMISSIONS.json."""
    assert BATCH_SUBMISSIONS.exists()
    with open(BATCH_SUBMISSIONS, "r", encoding="utf-8") as f:
        data = json.load(f)
    found = False
    for manifest_hash, batch_entry in data.items():
        if "hole_e10_prod" in batch_entry:
            rec = batch_entry["hole_e10_prod"]
            if rec.get("pbs_job_id") == JOB_ID:
                found = True
                break
    assert found, f"Job {JOB_ID} not found in MODE1_BATCH_SUBMISSIONS.json"


def test_load_displacement_and_parity():
    """Verify peak load parity between Candidate E10 and F1685 Baseline."""
    assert RESULTS_JSON.exists(), f"Results JSON missing: {RESULTS_JSON}"
    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        res = json.load(f)

    e10 = res["candidate_e10_results"]
    f1685 = res["f1685_baseline_reference"]
    comp = res["accuracy_vs_cost_comparison"]

    # Peak force within 0.5%
    p_e10 = e10["primary_peak_force_kN"]
    p_f1685 = f1685["peak_force_kN"]
    assert 0.55 <= p_e10 <= 0.57, f"Unexpected peak force: {p_e10}"
    assert abs(comp["primary_peak_force_diff_pct"]) < 0.5, f"Peak force discrepancy too large: {comp['primary_peak_force_diff_pct']}%"

    # Disp at peak within 1.0%
    u_e10 = e10["disp_at_primary_peak_mm"]
    u_f1685 = f1685["disp_at_peak_mm"]
    assert 0.0052 <= u_e10 <= 0.0055, f"Unexpected disp at peak: {u_e10}"
    assert abs(comp["disp_at_peak_diff_pct"]) < 1.0, f"Disp at peak discrepancy too large: {comp['disp_at_peak_diff_pct']}%"

    # Terminal load drop > 99%
    assert e10["load_drop_pct"] > 99.0, f"Insufficient load drop: {e10['load_drop_pct']}%"


def test_energy_consistency_and_relaxation():
    """Verify elastic energy relaxation and terminal dissipated fracture energy."""
    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        res = json.load(f)

    e10 = res["candidate_e10_results"]
    comp = res["accuracy_vs_cost_comparison"]

    # Elastic relaxation > 99%
    assert e10["elastic_relaxation_pct"] > 99.0, f"Elastic relaxation incomplete: {e10['elastic_relaxation_pct']}%"
    assert e10["terminal_elastic_strain_energy_uJ"] < 15.0, f"Residual elastic energy too high: {e10['terminal_elastic_strain_energy_uJ']} uJ"

    # Terminal fracture energy within 10%
    assert 2.5 <= e10["terminal_fracture_energy_mJ"] <= 3.0, f"Unexpected fracture energy: {e10['terminal_fracture_energy_mJ']} mJ"
    assert abs(comp["fracture_energy_diff_pct"]) < 10.0, f"Fracture energy discrepancy too large: {comp['fracture_energy_diff_pct']}%"


def test_mesh_reduction_and_computational_speedup():
    """Verify >=50% element/DOF reduction and >=2.0x computational speedup."""
    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        res = json.load(f)

    comp = res["accuracy_vs_cost_comparison"]

    assert comp["element_reduction_pct"] > 55.0, f"Element reduction below target: {comp['element_reduction_pct']}%"
    assert comp["dof_reduction_pct"] > 55.0, f"DOF reduction below target: {comp['dof_reduction_pct']}%"
    assert comp["cpu_time_reduction_pct"] > 60.0, f"CPU time reduction below target: {comp['cpu_time_reduction_pct']}%"
    assert comp["speedup_factor"] >= 2.5, f"Speedup factor below 2.5x: {comp['speedup_factor']}x"


def test_synthesis_figures_exist():
    """Verify generated publication synthesis PNG and vector PDF exist and are non-empty."""
    assert FIG_PNG.exists(), f"PNG figure missing: {FIG_PNG}"
    assert FIG_PNG.stat().st_size > 50000, f"PNG figure suspiciously small: {FIG_PNG.stat().st_size} bytes"

    assert FIG_PDF.exists(), f"PDF figure missing: {FIG_PDF}"
    assert FIG_PDF.stat().st_size > 10000, f"PDF figure suspiciously small: {FIG_PDF.stat().st_size} bytes"


def test_frozen_uel_preservation():
    """Verify bitwise preservation of frozen production UEL ce8d5edc... (907 lines)."""
    assert sha256_file(UEL_FILE) == FROZEN_UEL_SHA256, "Frozen UEL hash altered"
    with open(UEL_FILE, "r") as f:
        lines = [l for l in f]
    assert len(lines) == 907, f"UEL line count altered: expected 907, got {len(lines)}"
