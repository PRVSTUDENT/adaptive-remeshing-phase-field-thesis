#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Targeted regression test suite for Task F1596:
Independent Qualification and Conservation Audit of Package 72 Coupled State Transfer.
"""

import sys
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.postprocessing.extract_mode1_offset_results import evaluate_offset_simulation
from scripts.validation.evaluate_package72_state_transfer import run_comprehensive_audit

MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
PKG72_DIR = MODELS_DIR / "72_method_c_coupled_state_transfer"
PKG72_EV = PKG72_DIR / "evidence_1415199"


def test_package72_audit_execution_and_verdict():
    """Verify that the independent audit script executes and concludes PACKAGE72_C1-1_FAIL."""
    verdict = run_comprehensive_audit()
    assert verdict == "PACKAGE72_C1-1_FAIL"

    audit_json_path = PKG72_DIR / "PACKAGE72_STATE_TRANSFER_AUDIT.json"
    assert audit_json_path.is_file()
    with open(audit_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["task_id"] == "F1596"
    assert data["verdict"] == "PACKAGE72_C1-1_FAIL"
    assert "FORCE_CONTINUITY_DEFICIT" in data["primary_failure"]


def test_package72_force_continuity_deficit():
    """Verify force continuity discrepancy at checkpoint u = 0.00254 mm."""
    res72 = evaluate_offset_simulation(str(PKG72_EV), "M1_EXP_COUPLED_TRANSFER_650")
    rf_receiver = res72["step1_rf"]["rf2_N"]
    assert abs(rf_receiver - 1.748264) < 1e-5

    # Case A donor force at u = 0.00254 mm is 7.851239 N
    rf_donor_case_a = 7.8512395
    rel_error_case_a_pct = (rf_receiver - rf_donor_case_a) / rf_donor_case_a * 100.0
    assert abs(rel_error_case_a_pct - (-77.73)) < 0.1

    # Case B donor force at u = 0.00254 mm is 5.735525 N
    rf_donor_case_b = 5.7355247
    rel_error_case_b_pct = (rf_receiver - rf_donor_case_b) / rf_donor_case_b * 100.0
    assert abs(rel_error_case_b_pct - (-69.52)) < 0.1

    # Offline mapped linear reaction was 2.5736 N -> Step 1 dropped by 32.07%
    rf_mapped = 2.5736
    drop_pct = (rf_receiver - rf_mapped) / rf_mapped * 100.0
    assert abs(drop_pct - (-32.07)) < 0.1


def test_package72_healing_nodes_falsification():
    """Verify raw solver dat evidence falsifies the ledger PASS_ZERO_HEALING claim."""
    res72 = evaluate_offset_simulation(str(PKG72_EV), "M1_EXP_COUPLED_TRANSFER_650")
    d_metrics = res72["damage_step1"]

    assert d_metrics["healing_detected"] is True
    assert abs(d_metrics["min_delta_d"] - (-0.001661279)) < 1e-6
    assert d_metrics["healing_nodes_count"] == 291
    assert d_metrics["total_nodes"] == 713
    assert abs(d_metrics["healing_nodes_count"] / d_metrics["total_nodes"] * 100.0 - 40.8) < 0.2


def test_package72_energetic_discrepancies():
    """Verify elastic, fracture, and total energy discrepancies against donor."""
    res72 = evaluate_offset_simulation(str(PKG72_EV), "M1_EXP_COUPLED_TRANSFER_650")
    s1_energy = res72["step1_energy"]

    e_frac_receiver = s1_energy["e_fracture_mJ"]
    e_elas_receiver = s1_energy["e_elastic_mJ"]
    e_tot_receiver = s1_energy["e_total_mJ"]

    assert abs(e_frac_receiver - 0.34397864) < 1e-6
    assert abs(e_elas_receiver - 0.00222030) < 1e-6
    assert abs(e_tot_receiver - 0.34619894) < 1e-6

    # Donor energies from Package 50
    e_frac_donor = 0.29880935
    e_elas_donor = 0.00652335
    e_tot_donor = 0.30533271

    delta_e_frac_pct = (e_frac_receiver - e_frac_donor) / e_frac_donor * 100.0
    delta_e_elas_pct = (e_elas_receiver - e_elas_donor) / e_elas_donor * 100.0
    delta_e_tot_pct = (e_tot_receiver - e_tot_donor) / e_tot_donor * 100.0

    assert abs(delta_e_frac_pct - (+15.12)) < 0.1
    assert abs(delta_e_elas_pct - (-65.96)) < 0.1
    assert abs(delta_e_tot_pct - (+13.38)) < 0.1


def test_package72_continuation_softening_and_monotonicity():
    """Verify that Step 2 continuation exhibits physical softening and monotonic dissipation."""
    res72 = evaluate_offset_simulation(str(PKG72_EV), "M1_EXP_COUPLED_TRANSFER_650")
    assert res72["analysis_completed"] is True
    assert res72["dissipation_monotonic"] is True

    step2_rf = [r["rf2_N"] for r in res72["step2_rf_list"]]
    assert len(step2_rf) == 3
    # Monotonic softening in load
    assert step2_rf[0] > step2_rf[1] > step2_rf[2]
    assert abs(step2_rf[0] - 1.458) < 0.01
    assert abs(step2_rf[1] - 1.418) < 0.01
    assert abs(step2_rf[2] - 1.398) < 0.01
