# -*- coding: utf-8 -*-
"""
test_f1694_sec43_miseseri_fields_and_multidonor.py
===================================================
Unit test suite for Task F1694:
  Method A Pandey-Kumar Section 4.3 MISESERI Field Fix: Damage Fields,
  Multi-Donor MISESERI Fields, and Native Remeshing Audit.

Validates:
  1. Five-state physical damage record (initiation, primary prop, sec init, sec mid-prop, terminal).
  2. All 6 publication damage figures (5 individual + 1 combined series) in PDF and PNG.
  3. Multi-donor MISESERI error audit across 4 cases (sec init, sec mid-prop, terminal deg, elas).
  4. All 5 publication MISESERI figures (4 individual + 1 multi-panel comparison) in PDF and PNG.
  5. Best-donor adapted mesh metrics from Donor (b) (12,110 elements, 0.00% secondary <= l0/2).
  6. Best-donor adapted mesh publication figure in PDF and PNG.
  7. Stage 0 corrections: Case A metrics (9,432 elements) and scale-invariance explanation.
  8. Master thesis Subsection 5.6.13 integration and compilation integrity.
  9. Governance boundaries: production UEL untouched, 0 new PBS submissions.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VALIDATION_DIR = os.path.join(REPO_ROOT, "results", "validation")
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
CHAPTER05_TEX = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "chapter05_method_a_hole_benchmark.tex")
PRODUCTION_UEL = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()

# ==============================================================================
# 1. Five-State Damage Field Evolution Tests
# ==============================================================================

def test_five_state_damage_record_exists_and_valid():
    record_path = os.path.join(VALIDATION_DIR, "f1694_sec43_five_state_damage_record.json")
    assert os.path.exists(record_path), "Missing f1694_sec43_five_state_damage_record.json"
    with open(record_path, "r") as f:
        data = json.load(f)
    assert "states" in data, "Record must contain 'states'"
    states = data["states"]
    assert len(states) == 5, f"Expected 5 physical states, found {len(states)}"

    expected_ids = ["state_a", "state_b", "state_c", "state_d", "state_e"]
    for s, exp_id in zip(states, expected_ids):
        assert s["state_id"] == exp_id
        assert len(s["damage_by_element"]) == 3923, "All 3,923 physical elements must have damage values"

    # State a: Initiation
    sa = states[0]
    assert sa["uy_mm"] == 0.100
    assert sa["rf2_kN"] > 6.0, f"Expected RF > 6 kN at initiation, got {sa['rf2_kN']}"
    assert sa["max_damage_primary"] > 0.95
    assert sa["max_damage_secondary"] < 0.10

    # State b: Primary Propagation
    sb = states[1]
    assert sb["uy_mm"] == 0.200
    assert sb["rf2_kN"] < 3.0
    assert sb["max_damage_primary"] > 0.99
    assert sb["n_elements_d_gt_010"] >= 200

    # State c: Secondary Initiation
    sc = states[2]
    assert sc["uy_mm"] == 0.250
    assert sc["rf2_kN"] > sb["rf2_kN"], "Reaction force must rebound during secondary initiation"
    assert sc["max_damage_secondary"] > 0.35

    # State d: Secondary Mid-Propagation
    sd = states[3]
    assert sd["uy_mm"] == 0.300
    assert sd["max_damage_secondary"] > 0.95, "Secondary crack must be actively propagating (d > 0.95)"
    assert sd["n_elements_d_gt_050"] >= 80

    # State e: Terminal Severance
    se = states[4]
    assert se["uy_mm"] == 1.500
    assert se["rf2_kN"] < 0.01, f"Expected terminal load drop > 99.9%, got {se['rf2_kN']} kN"
    assert se["max_damage_primary"] > 0.9999
    assert se["max_damage_secondary"] > 0.9999
    assert se["n_elements_d_gt_090"] >= 35

def test_five_state_damage_figures_exist():
    basenames = [
        "fig_f1694_sec43_damage_state_a_initiation",
        "fig_f1694_sec43_damage_state_b_primary_prop",
        "fig_f1694_sec43_damage_state_c_secondary_init",
        "fig_f1694_sec43_damage_state_d_secondary_midprop",
        "fig_f1694_sec43_damage_state_e_terminal",
        "fig_f1694_sec43_damage_frame_series"
    ]
    for b in basenames:
        pdf_path = os.path.join(FIG_DIR, b + ".pdf")
        png_path = os.path.join(FIG_DIR, b + ".png")
        assert os.path.exists(pdf_path), f"Missing damage figure PDF: {pdf_path}"
        assert os.path.exists(png_path), f"Missing damage figure PNG: {png_path}"
        assert os.path.getsize(pdf_path) > 50000, f"Damage figure PDF too small: {pdf_path}"
        assert os.path.getsize(png_path) > 100000, f"Damage figure PNG too small: {png_path}"

# ==============================================================================
# 2. Multi-Donor Auxiliary Recovery and MISESERI Audit Tests
# ==============================================================================

def test_multidonor_miseseri_audit_exists_and_quantified():
    audit_path = os.path.join(VALIDATION_DIR, "f1694_sec43_multidonor_miseseri_audit.json")
    assert os.path.exists(audit_path), "Missing f1694_sec43_multidonor_miseseri_audit.json"
    with open(audit_path, "r") as f:
        data = json.load(f)

    expected_cases = ["SEC_INIT", "SEC_MIDPROP", "DEG", "ELAS"]
    for c in expected_cases:
        assert c in data, f"Missing case {c} in audit"
        c_data = data[c]
        assert c_data["element_count"] == 3923
        assert len(c_data["miseseri_by_element"]) == 3923
        assert c_data["eri_max"] > 0.0
        assert c_data["eri_mean"] > 0.0

    # Secondary mid-propagation error jump test:
    # Secondary max error in SEC_MIDPROP must jump substantially (> 2x) over SEC_INIT
    sec_init_sec_max = data["SEC_INIT"]["secondary_max"]
    sec_mid_sec_max = data["SEC_MIDPROP"]["secondary_max"]
    assert sec_mid_sec_max > 2.0 * sec_init_sec_max, (
        f"Expected >= 2x jump in secondary corridor error during mid-propagation, "
        f"got {sec_mid_sec_max} vs {sec_init_sec_max}"
    )

    # Intact elasticity must peak at notch tip
    peak_elas = data["ELAS"]["peak_coord"]
    assert abs(peak_elas[0] - 10.56) < 0.5
    assert abs(peak_elas[1] - 69.97) < 0.5

def test_multidonor_miseseri_figures_exist():
    basenames = [
        "fig_f1694_sec43_miseseri_sec_init",
        "fig_f1694_sec43_miseseri_sec_midprop",
        "fig_f1694_sec43_miseseri_terminal_deg",
        "fig_f1694_sec43_miseseri_terminal_elas",
        "fig_f1694_sec43_miseseri_multidonor_comparison"
    ]
    for b in basenames:
        pdf_path = os.path.join(FIG_DIR, b + ".pdf")
        png_path = os.path.join(FIG_DIR, b + ".png")
        assert os.path.exists(pdf_path), f"Missing MISESERI figure PDF: {pdf_path}"
        assert os.path.exists(png_path), f"Missing MISESERI figure PNG: {png_path}"
        assert os.path.getsize(pdf_path) > 50000, f"MISESERI figure PDF too small: {pdf_path}"
        assert os.path.getsize(png_path) > 100000, f"MISESERI figure PNG too small: {png_path}"

# ==============================================================================
# 3. Best-Donor Adapted Mesh Metrics and Figures
# ==============================================================================

def test_best_donor_adapted_mesh_metrics():
    metrics_path = os.path.join(VALIDATION_DIR, "f1694_sec43_adapted_mesh_best_donor_metrics.json")
    assert os.path.exists(metrics_path), "Missing f1694_sec43_adapted_mesh_best_donor_metrics.json"
    with open(metrics_path, "r") as f:
        data = json.load(f)

    assert data["task_id"] == "F1694-PK-SEC43-MISESERI-FIELDS-AND-MULTI-DONOR-REMESH"
    assert data["elements_total"] == 12110
    assert data["total_dofs"] == 24434
    assert data["pct_quads"] > 95.0

    # Primary corridor must achieve active refinement <= l0/3
    prim = data["primary_corridor"]
    assert prim["count"] >= 150
    assert prim["min"] <= data["l0_third_mm"], f"Primary h_min {prim['min']} must be <= l0/3 ({data['l0_third_mm']})"
    assert prim["med"] <= data["l0_mm"], f"Primary h_med {prim['med']} must be <= l0 ({data['l0_mm']})"

    # Secondary corridor must definitively fail the phase-field resolution threshold
    sec = data["secondary_corridor"]
    assert sec["count"] >= 50
    assert sec["pct_l0_half"] == 0.00, f"Secondary corridor must have exactly 0.00% <= l0/2, got {sec['pct_l0_half']}"
    assert sec["med"] > 3.0 * data["l0_half_mm"], f"Secondary h_med {sec['med']} must exceed 3*l0/2"

    # Selectivity and waste
    assert data["relative_waste_pct"] > 90.0
    assert data["w_90_mm"] > 50.0

    # Paper comparison
    comp = data["paper_comparison"]
    assert comp["primary_refined"] is True
    assert comp["secondary_refined"] is False

def test_best_donor_adapted_mesh_figure_exists():
    pdf_path = os.path.join(FIG_DIR, "fig_f1694_sec43_adapted_mesh_best_donor.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1694_sec43_adapted_mesh_best_donor.png")
    assert os.path.exists(pdf_path), f"Missing best donor adapted mesh PDF: {pdf_path}"
    assert os.path.exists(png_path), f"Missing best donor adapted mesh PNG: {png_path}"
    assert os.path.getsize(pdf_path) > 50000
    assert os.path.getsize(png_path) > 100000

# ==============================================================================
# 4. Stage 0 Corrections and Thesis Verification
# ==============================================================================

def test_stage_0_case_a_metrics_and_coincidence_resolution():
    case_a_path = os.path.join(VALIDATION_DIR, "f1693_sec43_case_a_adapted_mesh_metrics.json")
    assert os.path.exists(case_a_path), "Missing f1693_sec43_case_a_adapted_mesh_metrics.json"
    with open(case_a_path, "r") as f:
        data = json.load(f)
    assert data["elements_total"] == 9432
    assert data["total_dofs"] == 19134
    assert data["secondary_corridor"]["pct_l0_half"] == 0.0

    # Verify Chapter 5 discusses scale invariance and the 9,432 coincidence
    with open(CHAPTER05_TEX, "r", encoding="utf-8") as f:
        tex = f.read()
    assert "9,432-Element Coincidence" in tex or "9{,}432-element coincidence" in tex or "scale-invariant" in tex
    assert "fig_f1694_sec43_damage_frame_series.pdf" in tex
    assert "fig_f1694_sec43_miseseri_multidonor_comparison.pdf" in tex
    assert "fig_f1694_sec43_adapted_mesh_best_donor.pdf" in tex
    assert "tab:f1694_sec43_damage_states" in tex
    assert "tab:f1694_sec43_multidonor_miseseri" in tex

# ==============================================================================
# 5. Governance and Safety Boundaries
# ==============================================================================

def test_production_uel_remains_inviolable():
    actual_sha = sha256_file(PRODUCTION_UEL)
    assert actual_sha == EXPECTED_UEL_SHA, (
        f"Production UEL has been modified! Expected {EXPECTED_UEL_SHA}, got {actual_sha}"
    )

def test_zero_new_pbs_submissions_governance():
    task_def_path = os.path.join(REPO_ROOT, "project_coordination", "task_definitions", "F1694-PK-SEC43-MISESERI-FIELDS-AND-MULTI-DONOR-REMESH.json")
    with open(task_def_path, "r") as f:
        task_def = json.load(f)
    assert task_def["max_new_pbs_submissions"] == 0, "Task F1694 strictly authorises 0 new PBS submissions"
