# -*- coding: utf-8 -*-
import os
import json
import pytest
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_h20_physical_acceptance_failure():
    audit_path = os.path.join(REPO, "results", "validation", "h20_integrity_and_physical_failure_audit.json")
    assert os.path.exists(audit_path), "Audit JSON must exist"
    with open(audit_path, "r") as f:
        data = json.load(f)

    assert data["package134_classification"] == "H20_INVALID"
    assert data["package134_provisional_physical_verdict"] == "H20_FAILED_PHYSICAL"

    phys = data["package134_physical_acceptance_evaluation"]
    assert pytest.approx(phys["rf2_discrepancy_pct"], 0.01) == -63.37
    assert phys["rf2_passed"] is False

    assert pytest.approx(phys["e_tot_discrepancy_pct"], 0.01) == 67.30
    assert phys["e_tot_passed"] is False
    assert pytest.approx(phys["delta_e_tot_vs_h18_mJ"], 0.001) == 0.1518

def test_h20_column_indexing_defect_and_repair():
    bounds_csv = os.path.join(REPO, "models", "pandey_kumar_mode1", "134_c4_inc87_h20_underrelaxed_am_continuation", "d_lower_bounds.csv")
    with open(bounds_csv, "r") as f:
        header = [h.strip() for h in f.readline().strip().split(",")]

    assert header == ["EID", "D0_1", "D0_2", "D0_3", "D0_4", "H0_1", "H0_2", "H0_3", "H0_4"]

    driver_path = os.path.join(REPO, "models", "pandey_kumar_mode1", "134_c4_inc87_h20_underrelaxed_am_continuation", "driver_c4_inc87_h20_continuation.py")
    with open(driver_path, "r") as f:
        code = f.read()

    # The buggy driver parsed parts[1:5] instead of parts[5:9]
    assert "h_vals = [float(parts[1].strip()), float(parts[2].strip())" in code
    assert "float(parts[3].strip()), float(parts[4].strip())" in code

    # The repaired driver in R1 parsed H0_
    r1_driver_path = os.path.join(REPO, "models", "pandey_kumar_mode1", "134_r1_c4_inc87_h20_underrelaxed_am_continuation", "driver_c4_inc87_h20_continuation_r1.py")
    with open(r1_driver_path, "r") as f:
        r1_code = f.read()
    assert 'h_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]' in r1_code

def test_p134_r1_verification():
    audit_path = os.path.join(REPO, "results", "validation", "h20_integrity_and_physical_failure_audit.json")
    with open(audit_path, "r") as f:
        data = json.load(f)

    assert data["package134_r1_classification"] == "H20_R1_PASSED_PHYSICAL_AND_NUMERICAL"
    r1_phys = data["package134_r1_physical_acceptance_evaluation"]
    assert pytest.approx(r1_phys["rf2_discrepancy_pct"], 0.05) == -1.36
    assert r1_phys["rf2_passed"] is True
    assert pytest.approx(r1_phys["e_tot_discrepancy_pct"], 0.05) == 1.85
    assert r1_phys["e_tot_passed"] is True

    telemetry = data["active_set_telemetry_audit"]
    assert telemetry["package134_r1_free_nodes"] == 148
    assert telemetry["package134_r1_active_nodes"] == 4440
