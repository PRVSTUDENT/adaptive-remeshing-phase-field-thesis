#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn186_physical_validation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 186)
Protocol Version: 2

Unit test suite verifying the independent physical and energy validation
of Candidate Package 108 Revision 22 (108_r22_c3_adaptive_pdas_release)
against the compatible Case A roller-top reference.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

AUDIT_PATH = REPO_ROOT / "results/validation/mode1_f1597/r22_physical_validation_audit.json"
CASE_A_AUDIT_PATH = REPO_ROOT / "results/validation/mode1_f1597/r17_matched_boundary_reference_audit.json"
REF_D_PATH = REPO_ROOT / "results/validation/mode1_f1597/c3_case_a_plus_1nm_d.npy"
REF_U_PATH = REPO_ROOT / "results/validation/mode1_f1597/c3_case_a_plus_1nm_u.npy"

@pytest.fixture
def audit_data():
    assert AUDIT_PATH.exists(), f"Audit file does not exist: {AUDIT_PATH}"
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_01_artifact_schema_and_verdict(audit_data):
    """Test deliverable metadata, schema, and overall verdict."""
    assert audit_data["schema"] == 1
    assert audit_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert audit_data["turn"] == 186
    assert audit_data["verdict"] == "R22_C1_0B_FULLY_VERIFIED"
    assert audit_data["all_physical_passed"] is True
    assert "criteria" in audit_data
    assert "spatial_field_summary" in audit_data
    assert "energy_balance_summary" in audit_data
    assert "evidence_sources" in audit_data

def test_02_spatial_correlation_and_localization(audit_data):
    """Verify crack tip localization, spatial correlation R2, and L2 damage error."""
    crit = audit_data["criteria"]
    
    # C1: Crack-tip localization
    assert crit["c1_crack_tip_localization"]["passed"] is True
    assert crit["c1_crack_tip_localization"]["r22_tip_node"] == 1367
    assert crit["c1_crack_tip_localization"]["ref_tip_node"] == 1367

    # C2: Pearson R^2 correlation
    assert crit["c2_spatial_correlation_r2"]["passed"] is True
    assert crit["c2_spatial_correlation_r2"]["r_squared"] > 0.999
    assert crit["c2_spatial_correlation_r2"]["pearson_r"] > 0.999

    # C3: Relative L2 damage error
    assert crit["c3_relative_l2_damage_error"]["passed"] is True
    assert crit["c3_relative_l2_damage_error"]["l2_error_d"] < 0.050
    assert crit["c3_relative_l2_damage_error"]["mean_abs_error_d"] < 0.005

    # C4: Peak damage bounded
    assert crit["c4_peak_damage_physicality"]["passed"] is True
    assert 0.60 <= crit["c4_peak_damage_physicality"]["d_max_r22"] <= 0.75

def test_03_force_and_displacement_parity(audit_data):
    """Verify reaction force continuity and kinematics."""
    crit = audit_data["criteria"]
    
    # C5: Force continuity
    assert crit["c5_force_continuity"]["passed"] is True
    assert abs(crit["c5_force_continuity"]["diff_rf2_pct"]) <= 5.0
    assert pytest.approx(crit["c5_force_continuity"]["rf2_r22_N"], abs=1.0) == 178.23

    # Kinematics
    spatial = audit_data["spatial_field_summary"]
    assert spatial["l_inf_disp_error_mm"] < 1.0e-4
    assert spatial["l2_disp_relative_error"] < 0.010

def test_04_energy_components_and_conservation(audit_data):
    """Verify fracture energy, elastic strain energy, and external work parity."""
    crit = audit_data["criteria"]
    eb = audit_data["energy_balance_summary"]

    # C6: Fracture energy parity
    assert crit["c6_fracture_energy_parity"]["passed"] is True
    assert abs(crit["c6_fracture_energy_parity"]["diff_ef_pct"]) <= 5.0
    assert pytest.approx(crit["c6_fracture_energy_parity"]["e_frac_r22_mJ"], abs=1e-3) == 0.0631

    # C7: Elastic energy parity
    assert crit["c7_elastic_energy_parity"]["passed"] is True
    assert abs(crit["c7_elastic_energy_parity"]["diff_ee_pct"]) <= 5.0
    assert pytest.approx(crit["c7_elastic_energy_parity"]["e_elas_r22_mJ"], abs=1e-3) == 0.1752

    # C8: External work parity
    assert crit["c8_external_work_parity"]["passed"] is True
    assert abs(crit["c8_external_work_parity"]["diff_wext_pct"]) <= 2.0

    # Total internal energy conservation: 99.98% parity
    assert abs(eb["diff_etot_pct"]) < 0.10

def test_05_damage_band_morphology(audit_data):
    """Verify crack band width and node count profiles."""
    band = audit_data["spatial_field_summary"]["band_profile"]
    
    # Band counts at th=0.01 and th=0.10 match reference within 5 nodes
    assert abs(band["d_ge_0.01"]["count_diff"]) <= 5
    assert abs(band["d_ge_0.05"]["count_diff"]) <= 5
    assert abs(band["d_ge_0.10"]["count_diff"]) <= 5
    # Total node count is 2769
    assert audit_data["spatial_field_summary"]["total_nodes"] == 2769
