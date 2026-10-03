# -*- coding: utf-8 -*-
"""
Unit tests for Gate-6B Stage 12: Publication-supported non-uniform coarse-mesh
realization diagnostic and provenance audit on the Pandey-Kumar Mode-I benchmark.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STAGE12_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "98_mode1_stage12_nonuniform_coarse_diagnostic")
PHASE_A_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE12_PHASE_A_TOPOLOGY_AUDIT.json")
STAGE12_SUMMARY_JSON = os.path.join(STAGE12_DIR, "STAGE12_NONUNIFORM_COARSE_SUMMARY.json")
STAGE12_REPORT_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE12_NONUNIFORM_COARSE_REPORT.json")
STAGE12_REPORT_MD = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE12_NONUNIFORM_COARSE_REPORT.md")
PROVENANCE_AUDIT_JSON = os.path.join(STAGE12_DIR, "MODE1_STAGE12_PROVENANCE_AUDIT.json")
INF_CSV_PATH = os.path.join(STAGE12_DIR, "stage12_layered_inf_companion_miseseri.csv")
CONT_CSV_PATH = os.path.join(STAGE12_DIR, "stage12_continuum_control_miseseri.csv")
FIGURES_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode1_gate6b")

def test_phase_a_topology_audit():
    """Verify Phase A topology audit results for baseline 2,906 mesh."""
    assert os.path.exists(PHASE_A_JSON), "Phase A JSON must exist"
    with open(PHASE_A_JSON, "r") as f:
        data = json.load(f)
        
    assert data["total_elements"] == 2906
    assert data["quad_elements"] == 2818
    assert data["tri_elements"] == 88
    assert abs(data["quad_fraction"] - 0.9697) < 0.001
    assert abs(data["tri_fraction"] - 0.0303) < 0.001
    assert data["node_valence_distribution"]["4"] > 2000
    assert data["published_comparison_evidence"]["topology_mismatch_classification"] == "CURRENT_TOPOLOGY_PARTIALLY_CONSISTENT_WITH_PUBLISHED_NONUNIFORM_PATTERN"

def test_stage12_coarse_mesh_and_raw_miseseri():
    """Verify Phase B non-uniform coarse mesh and Phase C raw MISESERI analysis."""
    assert os.path.exists(STAGE12_SUMMARY_JSON), "Stage 12 summary JSON must exist"
    with open(STAGE12_SUMMARY_JSON, "r") as f:
        data = json.load(f)
        
    diag = data["coarse_mesh_diagnostic"]
    assert diag["total_elements"] == 3019
    assert diag["total_quads"] == 2940
    assert diag["total_tris"] == 79
    assert abs(diag["mean_h_eq_mm"] - 0.0180) < 0.002
    
    # Error field statistics
    stats = diag["miseseri_stats"]
    assert stats["max"] > 1000.0
    assert stats["min"] > 0.1
    
    # Regional shares: Far-field should contain a substantial portion (~48%)
    reg_shares = diag["regional_error_shares"]
    assert abs(reg_shares["far_field_share"] - 0.480) < 0.05
    assert abs(reg_shares["crack_tip_share"] - 0.339) < 0.05
    
    # Footprints
    fps = diag["footprints"]
    assert abs(fps["ge_01pct_fraction"] - 0.209) < 0.05
    assert fps["ge_001pct_fraction"] > 0.95
    
    assert diag["raw_miseseri_verdict"] == "NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_MISESERI_IMPROVEMENT"

def test_stage12_native_adaptive_remeshing():
    """Verify Phase D native 1% adaptive remeshing results on non-uniform mesh."""
    assert os.path.exists(STAGE12_SUMMARY_JSON), "Stage 12 summary JSON must exist"
    with open(STAGE12_SUMMARY_JSON, "r") as f:
        data = json.load(f)
        
    adapted = data["adapted_mesh"]
    assert adapted["total_elements"] == 139407
    assert adapted["total_nodes"] == 137958
    assert abs(adapted["h_eq_stats"]["median"] - 0.00213) < 0.0005
    
    # Spatial morphology: Far-field dominance
    morph = data["spatial_morphology"]
    assert morph["crack_corridor_count"] == 15796
    assert abs(morph["crack_corridor_fraction"] - 0.1133) < 0.02
    assert morph["far_field_total_count"] == 123611
    assert abs(morph["far_field_fraction"] - 0.8867) < 0.02
    
    # Bounding box of refined elements (covers essentially the full domain)
    bbox = morph["refined_bbox_h003"]
    assert bbox["count"] > 100000
    assert bbox["y_min"] < 0.01
    assert bbox["y_max"] > 0.99
    
    # Verdicts
    verdicts = data["verdicts"]
    assert verdicts["raw_miseseri_verdict"] == "NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_MISESERI_IMPROVEMENT"
    assert verdicts["adaptive_morphology_verdict"] == "NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_IMPROVEMENT"

def test_stage12_provenance_audit_and_datasets():
    """Verify Stage 12 provenance audit JSON and exported dataset CSVs."""
    assert os.path.exists(PROVENANCE_AUDIT_JSON), "Provenance audit JSON must exist"
    assert os.path.exists(INF_CSV_PATH), "Infinitesimal companion CSV must exist"
    assert os.path.exists(CONT_CSV_PATH), "Continuum control CSV must exist"
    
    with open(PROVENANCE_AUDIT_JSON, "r") as f:
        prov = json.load(f)
        
    assert prov["status"] == "PROVENANCE_AUDIT_COMPLETED"
    
    # Check infinitesimal companion metrics
    inf_metrics = prov["field_interrogation_statistics"]["infinitesimal_companion"]
    inf_max_eri = inf_metrics["miseseri_stats_kN_mm2"]["max"]
    assert 1e-15 < inf_max_eri < 1e-13, "Infinitesimal companion peak MISESERI must be order 10^-14"
    assert abs(inf_metrics["regional_shares"]["far_field_share"] - 0.4975) < 0.02
    assert inf_metrics["footprints_count"]["ge_001pct"] > 2800
    
    # Check continuum control metrics
    cont_metrics = prov["field_interrogation_statistics"]["continuum_control"]
    cont_max_eri = cont_metrics["miseseri_stats_MPa"]["max"]
    assert 1000.0 < cont_max_eri < 1500.0, "Continuum control peak MISESERI must be ~1170 MPa"
    assert abs(cont_metrics["regional_shares"]["far_field_share"] - 0.4804) < 0.02
    
    # Check correlation
    corr = prov["field_interrogation_statistics"]["cross_field_correlation"]
    assert corr > 0.95, "Correlation between normalized fields must exceed 0.95"
    
    # Check reclassification
    reclass = prov["provenance_verdict_and_reclassification"]
    assert reclass["remesh_139k_classification"] == "STAGE12_REMESH_WRONG_SOURCE_ODB"
    assert reclass["topology_branch_final_governing_verdict"] == "NOT_SUPPORTED_AS_DOMINANT_IN_TESTED_VARIANT"

def test_stage12_figures_exist():
    """Verify all Stage 12 figures are generated in both PNG and PDF formats."""
    expected_figures = [
        "mode1_stage12_fig1_phase_a_topology_audit.png",
        "mode1_stage12_fig1_phase_a_topology_audit.pdf",
        "mode1_stage12_fig2_miseseri_field_comparison.png",
        "mode1_stage12_fig2_miseseri_field_comparison.pdf",
        "mode1_stage12_fig3_adapted_morphology_comparison.png",
        "mode1_stage12_fig3_adapted_morphology_comparison.pdf"
    ]
    for fig_name in expected_figures:
        fig_path = os.path.join(FIGURES_DIR, fig_name)
        assert os.path.exists(fig_path), "Figure %s must exist" % fig_name

def test_stage12_report_and_artifacts():
    """Verify Stage 12 report files exist and maintain consistency."""
    assert os.path.exists(STAGE12_REPORT_MD), "Stage 12 Markdown report must exist"
    assert os.path.exists(STAGE12_REPORT_JSON), "Stage 12 JSON report must exist"
    
    with open(STAGE12_REPORT_JSON, "r") as f:
        rep = json.load(f)
        
    assert rep["audit_id"] == "GATE6B-STAGE12-NONUNIFORM-COARSE-DIAGNOSTIC-20261003"
    assert rep["verdicts"]["raw_miseseri_verdict"] == "NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_MISESERI_IMPROVEMENT"
    assert rep["verdicts"]["adaptive_morphology_verdict"] == "NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_IMPROVEMENT"
    assert rep["phase_b_coarse_mesh_construction"]["diagnostic_mesh_3019"]["total_elements"] == 3019
    assert rep["phase_d_native_adaptive_remeshing"]["adapted_mesh_139k"]["total_elements"] == 139407
    assert rep["provenance_and_source_integrity"]["remesh_139k_classification"] == "STAGE12_REMESH_WRONG_SOURCE_ODB"
