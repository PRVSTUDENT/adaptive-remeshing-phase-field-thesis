# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1725:
Physics-Driven Adaptive Mesh Reproduction of Pandey & Kumar (2025)
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "f1720_coarse_solution_audit.json")
SPATIAL_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "f1725_coarse_spatial_audit.json")
STUDY_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "217_f1725_physics_study", "f1725_physics_study_results.json")
F1725_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "217_f1725_physics_study", "F1725_S2_COARSEN_ET315.inp")
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

def test_coarse_terminal_displacement_reconciliation():
    assert os.path.exists(AUDIT_JSON), f"Missing audit json: {AUDIT_JSON}"
    with open(AUDIT_JSON) as f:
        data = json.load(f)
    u_term = data["terminal_displacement_mm"]
    assert abs(u_term - 0.00645141) < 1e-6, f"Terminal displacement {u_term} does not match 0.00645141 mm"
    # Check that Step 1 has 13 frames and Step 2 has 179 frames
    assert data["steps"]["Step-1"]["num_frames"] == 13
    assert data["steps"]["Step-2"]["num_frames"] == 179

def test_coarse_spatial_checkpoints():
    assert os.path.exists(SPATIAL_JSON), f"Missing spatial audit json: {SPATIAL_JSON}"
    with open(SPATIAL_JSON) as f:
        data = json.load(f)
    chks = data["checkpoints"]
    assert "Step1_End_Elastic_0p0050mm" in chks
    assert "Step2_Mid1_0p0057mm" in chks
    assert "Step2_Mid2_0p0062mm" in chks
    assert "Step2_Terminal_0p00645mm" in chks

    # In Step 1 (pure elastic), damage in all ligaments < 0.17
    assert chks["Step1_End_Elastic_0p0050mm"]["max_damage"] < 0.17
    # In Step 2 terminal, damage in Ligament 3 initiated (d > 0.50), while Lig 1 & 2 remain uncracked (d < 0.20)
    term = chks["Step2_Terminal_0p00645mm"]
    assert term["lig3_damage"]["max"] > 0.50, "Ligament 3 should have initiated crack (d > 0.50)"
    assert term["lig1_damage"]["max"] < 0.20, "Ligament 1 must remain elastic (d < 0.20)"
    assert term["lig2_damage"]["max"] < 0.20, "Ligament 2 must remain elastic (d < 0.20)"

def test_f1725_candidate_mesh_existence_and_parity():
    assert os.path.exists(STUDY_JSON), f"Missing study json: {STUDY_JSON}"
    with open(STUDY_JSON) as f:
        study = json.load(f)
    assert "F1725_S2_COARSEN_ET315" in study
    opt = study["F1725_S2_COARSEN_ET315"]["metrics"]
    
    # Target elements = 12,944
    n_elems = opt["num_elements"]
    assert n_elems == 13017, f"Expected 13,017 elements, got {n_elems}"
    parity_pct = 100.0 * (n_elems - 12944) / 12944.0
    assert abs(parity_pct) <= 1.0, f"Parity difference {parity_pct:.2f}% exceeds 1.0%"

    # Quad percentage >= 97%
    assert opt["quad_percentage"] >= 97.0, f"Quad percentage {opt['quad_percentage']}% < 97%"
    # 100% strictly positive Jacobians
    assert opt["positive_jacobians"] is True
    # Aspect ratio < 10
    assert opt["ar_max"] < 10.0

def test_f1725_bulk_preservation_and_reduced_spreading():
    with open(STUDY_JSON) as f:
        study = json.load(f)
    opt = study["F1725_S2_COARSEN_ET315"]["metrics"]
    uncoarsened = study["F1725_S2_ET345"]["metrics"]
    
    # Bulk elements should be reduced by at least 20% in coarsened model
    b_opt = opt["bulk"]["count"]
    b_uncoarsen = uncoarsened["bulk"]["count"]
    assert b_opt < b_uncoarsen
    reduction_pct = 100.0 * (b_uncoarsen - b_opt) / float(b_uncoarsen)
    assert reduction_pct >= 20.0, f"Bulk reduction {reduction_pct:.2f}% < 20%"
    
    # Bulk mean size should be larger in coarsened model (closer to 20 um background)
    assert opt["bulk"]["mean"] > uncoarsened["bulk"]["mean"]
    assert opt["bulk"]["mean"] >= 16.0, f"Bulk mean size {opt['bulk']['mean']} um < 16.0 um"

def test_f1725_ligament_centerline_resolution():
    with open(STUDY_JSON) as f:
        study = json.load(f)
    opt = study["F1725_S2_COARSEN_ET315"]["metrics"]
    profs = opt["centerline_profiles"]
    
    # Ligament 3 (33.1 um gap) must be uniformly refined <= l0/3 (2.67 um)
    lig3_bins = profs["Ligament 3"]["profile_bins"]
    for b in lig3_bins:
        assert b <= 2.67, f"Ligament 3 element size {b} um exceeds l0/3"
        
    # Ligaments 1, 2, 4 must have fine elements near hole flanks (<= l0/2 = 4.0 um)
    lig1_bins = profs["Ligament 1"]["profile_bins"]
    assert lig1_bins[0] <= 4.0, f"Ligament 1 void flank size {lig1_bins[0]} um > 4.0 um"
    assert lig1_bins[-1] <= 4.0, f"Ligament 1 void flank size {lig1_bins[-1]} um > 4.0 um"
    
    # Ligament 1 midpoint exhibits elastic saddle (h > 6.0 um)
    assert lig1_bins[4] > 6.0, f"Ligament 1 midpoint size {lig1_bins[4]} um should exhibit saddle > 6.0 um"

def test_f1725_input_deck_validity():
    assert os.path.exists(F1725_INP), f"Missing INP deck: {F1725_INP}"
    with open(F1725_INP) as f:
        content = f.read().upper()
    assert "*NODE" in content
    assert "*ELEMENT" in content
    assert len(content.splitlines()) > 1000

def test_f1725_figures_generated():
    fig_names = [
        "fig_f1725_figure_1_five_way_mesh_comparison",
        "fig_f1725_figure_2_four_ligament_zoom_matrix",
        "fig_f1725_figure_3_centerline_profiles",
        "fig_f1725_figure_4_spatial_metrics_and_bulk_audit",
        "fig_f1725_figure_5_checkpoint_error_field_comparison"
    ]
    for fn in fig_names:
        for folder in ["figures/pandey_kumar_fig22_25_reproduction", "MA_AdaptiveRemeshing_Report_2026/figures"]:
            pdf_path = os.path.join(REPO_ROOT, folder, fn + ".pdf")
            png_path = os.path.join(REPO_ROOT, folder, fn + ".png")
            assert os.path.exists(pdf_path), f"Missing figure PDF: {pdf_path}"
            assert os.path.exists(png_path), f"Missing figure PNG: {png_path}"
            assert os.path.getsize(pdf_path) > 1000
            assert os.path.getsize(png_path) > 1000

def test_zero_hpc_submissions_gate():
    assert os.path.exists(ACTIVE_TASK_JSON)
    with open(ACTIVE_TASK_JSON) as f:
        t = json.load(f)
    if t.get("task_id") != "F1725-PHYSICS-DRIVEN-ADAPTIVE-MESH-REPRODUCTION":
        pytest.skip("Test specifically guards Task F1725 zero HPC submissions gate; active task is %s" % t.get("task_id"))
    assert t["max_new_pbs_submissions"] == 0
    assert t["submissions_consumed"] == 0
