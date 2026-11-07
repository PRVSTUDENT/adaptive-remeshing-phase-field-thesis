#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_same_mesh_transfer_diagnostic.py
=====================================
Unit & regression test suite for Method C Same-Mesh Transfer Diagnostic.
Task: F1619-METHOD-C-SAME-MESH-TRANSFER-DIAGNOSTIC-FORMULATION
Protocol Version: 2

Validates:
1. Exact nodal displacement identity on same mesh (B1 vs B0: max ||Delta u|| <= 1e-9 mm).
2. Exact nodal damage identity on same mesh (B1 vs B0: max |Delta d| <= 1e-5).
3. Causal proof of history intra-element gradient flattening (B1 vs B0: max |Delta H| > 1.0 MPa, spread > 10.0 MPa).
4. Spatial crack-tip localization (confinement to r <= 2 um).
5. Diagnostic JSON summary schema, metrics, and markdown report completeness.
"""

from __future__ import print_function, division
import json
import math
import os
import sys
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SUMMARY_JSON_PATH = REPO_ROOT / "results/validation/same_mesh_transfer_diagnostic_summary.json"
REPORT_MD_PATH = REPO_ROOT / "results/validation/same_mesh_transfer_diagnostic_report.md"


@pytest.fixture(scope="module")
def diagnostic_data():
    """Loads precomputed diagnostic summary JSON."""
    assert SUMMARY_JSON_PATH.is_file(), f"Missing summary JSON: {SUMMARY_JSON_PATH}"
    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def test_diagnostic_metadata_and_governance(diagnostic_data):
    """Verifies task ID, governance, and zero-PBS enforcement."""
    assert diagnostic_data["schema"] == 1
    assert diagnostic_data["task_id"] == "F1619-METHOD-C-SAME-MESH-TRANSFER-DIAGNOSTIC-FORMULATION"
    gov = diagnostic_data["governance"]
    assert gov["protocol_version"] == 2
    assert gov["zero_pbs_enforced"] is True
    assert "HND-aab573d5c0bd" in gov["authorized_by"]


def test_four_configuration_suite_specifications(diagnostic_data):
    """Verifies that Configurations A, B0, B1, and C are registered with correct discretization counts."""
    configs = diagnostic_data["configurations"]
    assert "A_donor_source" in configs
    assert "B0_exact_copy" in configs
    assert "B1_transfer_pipeline" in configs
    assert "C_nonmatching_c6" in configs

    # Donor C5 mesh has exactly 12,996 elements and 13,278 physical nodes (+ RP 999999)
    assert configs["A_donor_source"]["elements_quad"] == 12996
    assert configs["A_donor_source"]["nodes_physical"] == 13278
    assert configs["A_donor_source"]["reference_point_id"] == 999999
    assert abs(configs["A_donor_source"]["target_uy_mm"] - 0.0018703125) < 1e-7

    # Configuration B0 has identical counts
    assert configs["B0_exact_copy"]["elements_quad"] == 12996
    assert configs["B0_exact_copy"]["nodes_physical"] == 13278
    assert configs["B0_exact_copy"]["reference_point_id"] == 999999

    # Configuration B1 has identical counts and zero healing/bounds violations
    assert configs["B1_transfer_pipeline"]["elements_quad"] == 12996
    assert configs["B1_transfer_pipeline"]["nodes_physical"] == 13278
    assert configs["B1_transfer_pipeline"]["reference_point_id"] == 999999
    assert configs["B1_transfer_pipeline"]["healing_violations"] == 0
    assert configs["B1_transfer_pipeline"]["bounds_violations"] == 0

    # Configuration C is C6 with 15,252 elements and 15,559 nodes
    assert configs["C_nonmatching_c6"]["mesh_elements"] == 15252
    assert configs["C_nonmatching_c6"]["mesh_nodes"] == 15559


def test_nodal_displacement_identity_on_same_mesh(diagnostic_data):
    """Asserts that nodal displacement transfer on identical mesh is exact to <= 1e-9 mm."""
    disp = diagnostic_data["quantitative_comparison_b1_vs_b0"]["displacement"]
    assert disp["max_delta_u_norm_mm"] <= 1e-9
    assert disp["rms_delta_u_norm_mm"] <= 1e-9
    assert disp["tolerance_exceeded_count"] == 0
    assert disp["tolerance_exceeded_pct"] == 0.0


def test_nodal_damage_identity_on_same_mesh(diagnostic_data):
    """Asserts that nodal damage transfer on identical mesh is exact to <= 1e-5."""
    dmg = diagnostic_data["quantitative_comparison_b1_vs_b0"]["damage"]
    assert dmg["max_delta_d"] <= 1e-5
    assert dmg["rms_delta_d"] <= 1e-5
    assert dmg["tolerance_exceeded_count"] == 0
    assert dmg["tolerance_exceeded_pct"] == 0.0


def test_gauss_point_history_intra_element_gradient_flattening(diagnostic_data):
    """
    Asserts the primary causal discovery:
    Element-averaged history transfer creates an immediate multi-MPa perturbation
    due to flattening steep crack-tip within-element gradients.
    """
    hist = diagnostic_data["quantitative_comparison_b1_vs_b0"]["history"]
    
    # Max error exceeds coupled tolerance (1e-4 MPa) by orders of magnitude
    assert hist["max_delta_H_MPa"] > 1.0, f"Expected multi-MPa perturbation, got {hist['max_delta_H_MPa']}"
    assert abs(hist["max_delta_H_MPa"] - 6.3491) < 0.01
    
    # Max intra-element history gradient exceeds 10 MPa
    assert hist["max_intra_element_range_MPa"] > 10.0
    assert abs(hist["max_intra_element_range_MPa"] - 12.3560) < 0.01
    assert hist["max_intra_element_id"] == 6437
    
    # Peak GP history loss is substantial (underestimating crack driving force)
    assert hist["max_history_loss_at_peak_gp_MPa"] > 5.0
    assert abs(hist["max_history_loss_at_peak_gp_MPa"] - 6.3491) < 0.01

    # Over 50% of all Gauss points exceed 1e-4 MPa tolerance
    assert hist["gps_exceeding_tolerance_pct"] > 50.0
    assert hist["gps_exceeding_tolerance_count"] == 34720
    assert hist["gps_exceeding_1MPa_count"] == 20


def test_crack_tip_spatial_localization(diagnostic_data):
    """Asserts that history perturbation is hyper-localized near crack tip (r <= 2 um)."""
    spatial = diagnostic_data["quantitative_comparison_b1_vs_b0"]["spatial_localization"]
    
    # Zone 1 (r <= 2 um) experiences severe multi-MPa error
    assert spatial["zone_2um"]["max_delta_H_MPa"] > 5.0
    assert spatial["zone_2um"]["rms_delta_H_MPa"] > 0.5
    
    # Zone 2 (2 < r <= 5 um) drops by an order of magnitude
    assert spatial["zone_5um"]["max_delta_H_MPa"] < 1.0
    
    # Zone 3 (5 < r <= 10 um) drops below 0.05 MPa
    assert spatial["zone_10um"]["max_delta_H_MPa"] < 0.05
    
    # Far-field RMS is small
    assert spatial["zone_far_field"]["rms_delta_H_MPa"] < 0.01


def test_causal_conclusions_and_report_file(diagnostic_data):
    """Verifies causal conclusion statements and existence of markdown report."""
    causal = diagnostic_data["causal_conclusions"]
    assert causal["displacement_conservatism"] == "CONSERVATIVE"
    assert causal["damage_conservatism"] == "CONSERVATIVE"
    assert causal["history_averaging_perturbation"] == "SEVERE_INTRA_ELEMENT_FLATTENING"
    assert causal["max_history_perturbation_vs_tol_ratio"] > 50000.0

    assert REPORT_MD_PATH.is_file()
    with open(REPORT_MD_PATH, "r", encoding="utf-8") as f:
        md = f.read()
    assert "F1619-METHOD-C-SAME-MESH-TRANSFER-DIAGNOSTIC-FORMULATION" in md
    assert "Element-Averaging Defect" in md
    assert "True Isoparametric Bilinear GP Interpolation" in md
