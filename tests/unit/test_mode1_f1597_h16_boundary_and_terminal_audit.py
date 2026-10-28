# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h16_boundary_and_terminal_audit.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Automated test suite verifying:
1. Boundary-card semantics and staggered AM active-set implementation for Package 131 R1.
2. Terminal evaluation metrics for Package 131 R1 (PBS Job 1418451.mmaster02).
3. Hypothesis H16 verdict (H16_FAILED_NONSTATIONARY).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "h16_boundary_card_and_active_set_audit.json")
SUMMARY_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "131_r1_c4_inc87_second_halfstep_h16_continuation", "c4_inc87_h16_continuation_summary.json")

@pytest.fixture(scope="module")
def audit_data():
    assert os.path.isfile(AUDIT_JSON), "Missing audit JSON: %s" % AUDIT_JSON
    with open(AUDIT_JSON, "r") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def summary_data():
    assert os.path.isfile(SUMMARY_JSON), "Missing summary JSON: %s" % SUMMARY_JSON
    with open(SUMMARY_JSON, "r") as f:
        return json.load(f)

def test_audit_overall_status(audit_data):
    assert audit_data["schema"] == 1
    assert audit_data["status"] == "PASS"
    assert audit_data["verification_passed"] is True
    assert audit_data["h16_verdict"] == "H16_FAILED_NONSTATIONARY"
    assert audit_data["pbs_job_id"] == "1418451.mmaster02"

def test_active_set_semantics(audit_data):
    sem = audit_data["active_set_semantics_audit"]
    assert sem["d_prescribed_type"] == "node_id_keyed_dict"
    assert sem["first_physical_node_id"] == 1
    assert sem["last_physical_node_id"] == 4588
    assert sem["rp_999999_excluded_from_damage_cards"] is True
    assert sem["pdas_phase_subproblem_free_nodes"] == 3848
    assert sem["pdas_phase_subproblem_active_nodes"] == 740
    assert sem["free_nodes_residual_satisfied"] is True
    assert sem["free_residual_max_kN_mm"] <= sem["free_residual_tolerance_kN_mm"]
    assert sem["active_multiplier_min_kN_mm"] >= sem["active_multiplier_tolerance_kN_mm"]
    assert sem["obsolete_constraints_overwritten_per_cycle"] is True
    assert sem["zero_damage_healing_violations"] == 0
    assert sem["committed_gp_histories_count"] == 17688
    assert sem["mechanical_boundary_conditions_preserved"] is True

def test_numerical_convergence_metrics(audit_data):
    num = audit_data["numerical_convergence_metrics"]
    assert num["cycles_completed"] == 25
    assert num["iteration_cap"] == 25
    assert num["iteration_cap_reached"] is True
    assert num["delta_d_final"] > num["delta_d_threshold"]  # 0.001445 > 0.001000
    assert num["damage_stationarity_passed"] is False
    assert num["delta_rf2_final_N"] <= num["delta_rf2_threshold_N"]  # 0.0886 <= 0.1 N
    assert num["force_stationarity_passed"] is True
    assert num["all_contraction_factors_sub_unity"] is True
    assert all(rho < 1.0 for rho in num["contraction_factors"])

def test_energetics_and_work_balance(audit_data):
    eng = audit_data["energetics_and_work_balance"]
    assert pytest.approx(eng["initial_midpoint_u_top_mm"], 1e-10) == 0.001938410627
    assert pytest.approx(eng["target_inc87_u_top_mm"], 1e-10) == 0.001947309589
    assert pytest.approx(eng["delta_u_mm"], 1e-10) == 0.0000088989616
    assert eng["delta_w_ext_mJ"] > 0.0
    assert eng["delta_e_tot_mJ"] > 0.0
    assert eng["whole_system_energy_residual_pct"] < 0.05

def test_donor_comparison_tolerances(audit_data):
    comp = audit_data["comparison_to_donor_inc87"]
    assert comp["rf2_within_5pct_tolerance"] is True
    assert comp["rf2_discrepancy_pct"] <= 5.0
    assert comp["e_tot_within_2pct_tolerance"] is True
    assert comp["e_tot_discrepancy_pct"] <= 2.0

def test_governance_preserved(audit_data):
    gov = audit_data["governance"]
    assert gov["stage_c1_2_step2_energy_gate_failed_binding"] is True
    assert gov["production_uel_preserved"] is True
    assert gov["no_c5_remeshing_without_authorization"] is True
