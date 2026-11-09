# -*- coding: utf-8 -*-
"""
tests/unit/test_f1702_figs14_16_reproduction.py
===============================================
Unit tests for Task F1702:
Complete Pandey-Kumar Figures 14-16 Reproduction, Physically Consistent
MISESERI Adaptive Remeshing, and Verified Fracture Continuation.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_f1702_specification_matrix():
    matrix_path = os.path.join(REPO_ROOT, "docs", "validation", "F1702_PAPER_TO_MODEL_SPECIFICATION_MATRIX.md")
    assert os.path.exists(matrix_path), "Specification matrix must exist"
    with open(matrix_path, "r") as f:
        content = f.read()
    assert "65.0" in content and "120.0" in content, "Plate dimensions must be 65 x 120 mm"
    assert "0.285" in content, "Regularization length l0 must be 0.285 mm"
    assert "210.0" in content, "Young's modulus must be 210.0 GPa"
    assert "FUTURE WORK" in content, "Must record that continuation is future work in Pandey & Kumar"

def test_f1702_gate_a_kinematic_and_constitutive_recovery():
    json_path = os.path.join(REPO_ROOT, "results", "validation", "f1702_integration_point_stress_recovery.json")
    assert os.path.exists(json_path), "Gate A evaluation JSON must exist"
    with open(json_path, "r") as f:
        data = json.load(f)
    s2 = data["states"]["STATE2"]
    assert s2["strain_reconstruction_accuracy"]["linf_norm_gamma12"] < 1.0e-4, "L_inf strain discrepancy must be <= 1e-4"
    assert s2["strain_reconstruction_accuracy"]["verdict"] == "KINEMATIC_STRAIN_RECONSTRUCTION_PASS"
    s5 = data["states"]["STATE5"]
    assert s5["pointwise_stress_extrema_MPa"]["max_mises"] < 1.0, "State 5 must show complete physical stress unloading (max Mises < 1 MPa)"

def test_f1702_gate_b_continuous_odbs_exist():
    odb_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "202_pk_sec43_continuous_recovery")
    for st in ["STATE2", "STATE4", "STATE5"]:
        odb_path = os.path.join(odb_dir, "PK_SEC43_CONTINUOUS_%s.odb" % st)
        assert os.path.exists(odb_path), "Continuous recovery ODB must exist: %s" % odb_path
        assert os.path.getsize(odb_path) > 1000000, "Continuous recovery ODB must be non-empty (>1 MB)"

def test_f1702_gate_c_miseseri_corridor_asymmetry():
    json_path = os.path.join(REPO_ROOT, "results", "validation", "f1702_continuous_recovery_and_miseseri.json")
    assert os.path.exists(json_path), "Gate C evaluation JSON must exist"
    with open(json_path, "r") as f:
        data = json.load(f)
    s2 = data["states"]["STATE2"]["gate_c_native_miseseri"]
    s4 = data["states"]["STATE4"]["gate_c_native_miseseri"]
    # Verify primary corridor error is much larger than secondary error due to stress relaxation
    assert s2["corridor_distribution"]["primary_corridor_max_MPa"] > 1000.0
    assert s4["corridor_distribution"]["primary_corridor_max_MPa"] > 1000.0
    assert s4["corridor_distribution"]["secondary_corridor_max_MPa"] < 100.0

def test_f1702_gate_d_sequential_refinement_gap_diagnosis():
    json_path = os.path.join(REPO_ROOT, "results", "validation", "f1702_sequential_refinement_gap_diagnosis.json")
    assert os.path.exists(json_path), "Gate D diagnosis JSON must exist"
    with open(json_path, "r") as f:
        data = json.load(f)
    finding = data["root_cause_diagnosis"]["finding_1_pass1_initial_discontinuity"]
    assert finding["pass1_elements_le_l0_half"] == 0
    assert finding["pass1_max_gap_mm"] > 20.0
    conclusion = data["root_cause_diagnosis"]["falsifiable_conclusion"]
    assert "NOT caused by coarsening" in conclusion

def test_f1702_gate_e_adapted_mesh_metrics():
    inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "202_pk_sec43_continuous_recovery", "PK_SEC43_F1702_HISTORY_AWARE_ADAPT.inp")
    assert os.path.exists(inp_path), "F1702 adapted mesh inp must exist"
    audit_path = os.path.join(REPO_ROOT, "results", "validation", "f1702_reconciled_connectivity_audit.json")
    assert os.path.exists(audit_path), "Reconciled corridor connectivity audit must exist"
    with open(audit_path, "r") as f:
        audit = json.load(f)
    sec = audit["secondary_corridor"]
    prim = audit["primary_corridor"]
    assert sec["element_count_metrics"]["fraction_le_l0_pct"] >= 60.0, "Secondary corridor must have >= 60% elements <= l0"
    assert sec["element_count_metrics"]["min_h_mm"] <= 0.285 / 4.0, "Secondary corridor must resolve h_min <= l0/4"
    assert sec["centerline_geometric_coverage_l0"]["centerline_coverage_pct"] >= 40.0, "Secondary corridor must achieve >= 40% 1D centerline coverage"
    assert prim["element_count_metrics"]["fraction_le_l0_pct"] >= 50.0, "Primary corridor must retain >= 50% elements <= l0 in F1702"
    assert prim["centerline_geometric_coverage_l0"]["centerline_coverage_pct"] >= 10.0, "Primary corridor must retain >= 10% 1D centerline coverage"
    assert audit["mesh_summary"]["quad_percentage"] > 90.0, "Adapted mesh must be >90% quads"

def test_f1702_gate_g_state_transfer_qualification():
    json_path = os.path.join(REPO_ROOT, "results", "validation", "f1702_state_transfer_qualification.json")
    assert os.path.exists(json_path), "Gate G qualification JSON must exist"
    with open(json_path, "r") as f:
        data = json.load(f)
    assert data["mesh_quality"]["negative_jacobians"] == 0, "Zero negative Jacobians allowed"
    assert data["mesh_quality"]["jacobian_positivity_pct"] == 100.0
    assert data["damage_projection"]["physical_bounds_verified"] is True
    assert data["damage_projection"]["irreversibility_preserved"] is True
    assert data["continuation_qualification_verdict"] == "OFFLINE_STATE_TRANSFER_QUALIFIED_PENDING_SEPARATE_HPC_RUN"

def test_f1702_synthesis_figure_and_performance_comparison():
    pdf_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1702_pandey_kumar_figs14_16_synthesis.pdf")
    assert os.path.exists(pdf_path), "Synthesis PDF figure must exist"
    assert os.path.getsize(pdf_path) > 50000, "Synthesis PDF figure must be > 50 KB"

    perf_path = os.path.join(REPO_ROOT, "results", "validation", "f1702_computational_performance_comparison.json")
    assert os.path.exists(perf_path), "Computational performance comparison JSON must exist"
    with open(perf_path, "r") as f:
        perf = json.load(f)
    assert "models" in perf
    assert "coarse_job1_baseline" in perf["models"]
    assert "f1702_two_branch_preserved_adapt" in perf["models"]
