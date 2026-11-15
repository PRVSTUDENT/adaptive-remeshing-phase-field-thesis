# -*- coding: utf-8 -*-
"""
test_f1737_completion_inventory.py
Unit tests validating the read-only audit of Cases 1 to 5 under Master Objective F1737.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_case1_mesh_and_fracture_artifacts():
    # Case 1 F1738 mesh
    mesh_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "PK_F1738_CASE_1_ADAPT_PHYS.inp")
    assert os.path.isfile(mesh_path), f"Case 1 mesh missing at {mesh_path}"
    
    # Case 1 F1738 audit receipt
    audit_path = os.path.join(REPO_ROOT, "results", "validation", "f1738_case1_ligament_spatial_audit.json")
    assert os.path.isfile(audit_path)
    with open(audit_path, "r") as f:
        audit = json.load(f)
    assert audit["total_elements"] == 13960
    assert audit["quad_count"] == 13611
    assert audit["tri_count"] == 349
    assert audit["overall_area_compliance_pct_half_l0"] == 100.0
    assert audit["negative_jacobian_count"] == 0

    # Case 1 F1739 fracture summary
    summary_path = os.path.join(REPO_ROOT, "results", "validation", "f1739_case1_fracture_summary.json")
    assert os.path.isfile(summary_path)
    with open(summary_path, "r") as f:
        summary = json.load(f)
    comp = summary["benchmark_comparison"]
    assert comp["post_peak_load_drop_pct"] >= 99.9
    assert comp["f_max_N"] > 700.0
    energy = summary["thermodynamic_energy_balance"]
    assert energy["energy_imbalance_pct"] < 5.0
    assert energy["fracture_dissipation_monotonic"] is True
    assert summary["convergence_telemetry"]["total_cutbacks"] == 0

def test_case2_mesh_and_fracture_artifacts():
    # Case 2 F1734 mesh
    mesh_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "224_f1734_case2_distal_refinement", "PK_F1728_CASE_2_ADAPT_PHYS.inp")
    assert os.path.isfile(mesh_path)
    
    # Case 2 continuation audit
    cont_path = os.path.join(REPO_ROOT, "results", "validation", "f1753_case2_continuation_audit.json")
    assert os.path.isfile(cont_path)
    with open(cont_path, "r") as f:
        cont = json.load(f)
    assert cont["task_id"] == "F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION"
    assert cont["total_physical_elements"] == 23965
    assert "GATE_G4_GLOBAL_HISTORY_MONOTONICITY" in cont["gates"]
    assert cont["gates"]["GATE_G4_GLOBAL_HISTORY_MONOTONICITY"]["status"] == "PASS"

    # Case 2 indicator evidence summary
    ind_path = os.path.join(REPO_ROOT, "results", "validation", "f1756_case2_authentic_indicator_summary.json")
    assert os.path.isfile(ind_path)
    with open(ind_path, "r") as f:
        ind = json.load(f)
    assert ind["task_id"] == "F1756-CASE2-AUTHENTIC-INDICATOR-AND-SIZING-EVIDENCE"
    assert "donor_indicator_regions" in ind
    assert "adapted_mesh_composite_compliance" in ind

def test_case4_case5_mesh_artifacts_and_unexecuted_fracture():
    # Case 4 F1725 mesh
    c4_mesh = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "217_f1725_physics_study", "F1725_S2_COARSEN_ET315.inp")
    assert os.path.isfile(c4_mesh)

    # Case 5 F1726 mesh
    c5_mesh = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp")
    assert os.path.isfile(c5_mesh)

def test_figure_artifacts_existence():
    expected_figures = [
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1738_case1_ligament_comparison.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1739_case1_fracture_response.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1736_case_1_standalone_mesh.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1736_case_2_standalone_mesh.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1753_continuation_response.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1736_case_3_standalone_mesh.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1736_case_4_standalone_mesh.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1736_case_5_standalone_mesh.png"),
        os.path.join(REPO_ROOT, "results", "figures", "fig_f1736_five_case_comparison_corrected.png"),
    ]
    for fig in expected_figures:
        assert os.path.isfile(fig), f"Figure missing: {fig}"
        assert os.path.getsize(fig) > 1000, f"Figure empty: {fig}"
