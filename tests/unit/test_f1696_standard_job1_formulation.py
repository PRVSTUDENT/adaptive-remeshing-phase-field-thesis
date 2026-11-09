# -*- coding: utf-8 -*-
"""
test_f1696_standard_job1_formulation.py
========================================
Unit test suite for Task F1696:
  Pandey-Kumar Section 4.3 Job-1 Formulation Test: Standard-Element Job-1 MISESERI Band
  Resolving Handoff HND-F1696-JOB1-FORMULATION-001.

Validates:
  1. Standard-Element Job-1 model and deck integrity (CPS4R/CPS3, linear elasticity, 4500 incs).
  2. PBS Job-1 execution record (PBS Job 1421442.mmaster02, Exit 0, 4,500 increments).
  3. MISESERI audit JSON and scale invariance across all sampled frames (7.56% max, 1.70% mean).
  4. Pre-declared band criteria evaluation: Criteria (a), (b), (c) all FAIL -> Band Absent.
  5. Quantitative side-by-side comparison with Case A (Plane Strain vs Plane Stress).
  6. Generated publication figures exist and are valid.
  7. Governance and resource integrity: production UEL bitwise preserved, max 1 PBS job consumed.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VALIDATION_DIR = os.path.join(REPO_ROOT, "results", "validation")
FIGURES_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "196_pk_sec43_standard_element_job1")
PRODUCTION_UEL = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()

# ==============================================================================
# 1. Standard-Element Job-1 Model and Deck Integrity
# ==============================================================================

def test_f1696_standard_job1_model_and_deck_integrity():
    inp_path = os.path.join(MODEL_DIR, "PK_SEC43_STANDARD_JOB1.inp")
    assert os.path.exists(inp_path), f"Missing {inp_path}"

    with open(inp_path, "r") as f:
        content = f.read()

    # Must be standard elements, plane stress CPS4R and CPS3
    assert "TYPE=CPS4R" in content
    assert "TYPE=CPS3" in content
    assert "*USER ELEMENT" not in content, "Standard element Job-1 must not contain UEL"

    # Elastic material definition
    assert "*ELASTIC" in content
    assert "210000" in content or "210000." in content or "2.1e" in content or "210.0" in content

    # Two static steps totaling 4,500 increments
    assert content.count("*STEP") == 2
    assert "2000" in content  # Step 1 max incs
    assert "2500" in content  # Step 2 max incs

    # Output requests must include MISESERI, MISESAVG
    assert "MISESERI" in content
    assert "MISESAVG" in content

# ==============================================================================
# 2. PBS Job-1 Execution Record
# ==============================================================================

def test_f1696_pbs_job_execution_record():
    sta_path = os.path.join(MODEL_DIR, "PK_SEC43_STANDARD_JOB1.sta")
    assert os.path.exists(sta_path), f"Missing {sta_path}"

    with open(sta_path, "r") as f:
        sta_text = f.read()

    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta_text
    assert "2500" in sta_text

    # Check HPC_JOB_LEDGER.csv
    ledger_path = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
    with open(ledger_path, "r") as f:
        ledger_text = f.read()

    assert "1421442.mmaster02" in ledger_text
    assert "M1_PK_SEC43_STANDARD_JOB1" in ledger_text
    assert "COMPLETED,0" in ledger_text

# ==============================================================================
# 3. MISESERI Audit JSON and Scale Invariance
# ==============================================================================

def test_f1696_miseseri_audit_scale_invariance():
    audit_path = os.path.join(VALIDATION_DIR, "f1696_sec43_standard_job1_miseseri_audit.json")
    assert os.path.exists(audit_path), f"Missing {audit_path}"

    with open(audit_path, "r") as f:
        data = json.load(f)

    assert "CPS4R" in data["element_formulation"]
    assert "plane-stress" in data["element_formulation"]

    sampled = data["sampled_frames"]
    assert len(sampled) >= 6

    # Test scale invariance across all frames
    for key, frame in sampled.items():
        disp = frame["displacement_uy_mm"]
        sec = frame["secondary_corridor"]
        # Sec_max as percentage of peak must be ~7.56%
        assert abs(sec["max_pct_of_peak"] - 7.56) < 0.1, (
            f"Frame {key} at {disp} mm has unexpected max_pct_of_peak {sec['max_pct_of_peak']}"
        )
        # Sec_mean relative error must be ~1.70%
        assert abs(sec["mean_rel_error_pct"] - 1.70) < 0.1, (
            f"Frame {key} at {disp} mm has unexpected mean_rel_error_pct {sec['mean_rel_error_pct']}"
        )

# ==============================================================================
# 4. Pre-Declared Band Criteria Evaluation
# ==============================================================================

def test_f1696_predeclared_band_criteria():
    audit_path = os.path.join(VALIDATION_DIR, "f1696_sec43_standard_job1_miseseri_audit.json")
    with open(audit_path, "r") as f:
        data = json.load(f)

    eval_crit = data["predeclared_band_criteria_evaluation"]

    # Criterion (a): Secondary max >= 30% of peak (Measured 7.56%) -> FAIL
    assert eval_crit["criterion_a"]["verdict"] == "FAIL"
    assert abs(eval_crit["criterion_a"]["measured_value_pct"] - 7.56) < 0.1

    # Criterion (b): Secondary mean rel >= 10% (Measured 1.70%) -> FAIL
    assert eval_crit["criterion_b"]["verdict"] == "FAIL"
    assert abs(eval_crit["criterion_b"]["measured_value_pct"] - 1.70) < 0.1

    # Criterion (c): Continuous elevated-error band along both branches -> FAIL
    assert eval_crit["criterion_c"]["verdict"] == "FAIL"

    # Overall verdict
    assert eval_crit["overall_stage_c_band_verdict"] == "FAIL"
    assert "ABSENT" in eval_crit["scientific_conclusion"]
    assert "FALSIFIED" in eval_crit["scientific_conclusion"]

# ==============================================================================
# 5. Side-by-Side Quantitative Comparison with Case A
# ==============================================================================

def test_f1696_comparison_with_case_a():
    audit_path = os.path.join(VALIDATION_DIR, "f1696_sec43_standard_job1_miseseri_audit.json")
    with open(audit_path, "r") as f:
        data = json.load(f)

    comp = data["side_by_side_comparison_at_uy_1p46mm"]
    case_a = comp["f1693_case_a_plane_strain_cpe4"]
    f1696 = comp["f1696_standard_job1_plane_stress_cps4r"]

    # Index 5 is "Secondary max % of Peak"
    case_a_pct = case_a[5]
    f1696_pct = f1696[5]

    # Index 8 is "Secondary mean relative error %"
    case_a_mean_rel = case_a[8]
    f1696_mean_rel = f1696[8]

    # Case A metrics: 5.39% max, 1.73% mean
    assert abs(case_a_pct - 5.39) < 0.1
    assert abs(case_a_mean_rel - 1.73) < 0.1

    # F1696 metrics: 7.56% max, 1.70% mean
    assert abs(f1696_pct - 7.56) < 0.1
    assert abs(f1696_mean_rel - 1.70) < 0.1

    # Both are far below the 30% / 10% thresholds
    assert case_a_pct < 10.0
    assert f1696_pct < 10.0

# ==============================================================================
# 6. Generated Publication Figures Exist and Valid
# ==============================================================================

def test_f1696_figures_exist():
    fig1_pdf = os.path.join(FIGURES_DIR, "fig_f1696_sec43_miseseri_standard_job1.pdf")
    fig1_png = os.path.join(FIGURES_DIR, "fig_f1696_sec43_miseseri_standard_job1.png")
    fig2_pdf = os.path.join(FIGURES_DIR, "fig_f1696_sec43_miseseri_formulation_comparison.pdf")
    fig2_png = os.path.join(FIGURES_DIR, "fig_f1696_sec43_miseseri_formulation_comparison.png")

    for p in [fig1_pdf, fig1_png, fig2_pdf, fig2_png]:
        assert os.path.exists(p), f"Missing figure: {p}"
        assert os.path.getsize(p) > 10000, f"Figure file unusually small: {p}"

# ==============================================================================
# 7. Governance, UEL Preservation, and PBS Resource Policy
# ==============================================================================

def test_f1696_governance_and_resource_limits():
    # Production UEL must remain bitwise untouched
    assert sha256_file(PRODUCTION_UEL) == EXPECTED_UEL_SHA, "Production UEL was modified!"

    # Active task check
    active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task_path, "r") as f:
        active_task = json.load(f)

    assert active_task["task_id"] == "F1696-PK-SEC43-STANDARD-ELEMENT-JOB1-FORMULATION-TEST"
    assert active_task["max_new_pbs_submissions"] == 1
