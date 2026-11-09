# -*- coding: utf-8 -*-
"""
test_f1705_candidate_e10_evidence_reconciliation.py
===================================================
Unit regression tests for Task F1705 Candidate E10 Evidence Reconciliation
resolving review handoff HND-F1705-HOLE-E10-PROD-CLOSEOUT-001 (INSUFFICIENT_EVIDENCE)
qualifications Q1 through Q6.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RECON_PATH = REPO_ROOT / "results" / "validation" / "f1705_candidate_e10_evidence_reconciliation.json"
RESULTS_PATH = REPO_ROOT / "results" / "validation" / "f1705_candidate_e10_production_results.json"


@pytest.fixture(scope="module")
def recon_data():
    assert RECON_PATH.exists(), f"Reconciliation JSON missing at {RECON_PATH}"
    with open(RECON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def prod_results():
    assert RESULTS_PATH.exists(), f"Production results JSON missing at {RESULTS_PATH}"
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_q1_increment_accounting(recon_data):
    """Q1: Verify exact increment accounting reconciling 341 converged vs 342 attempted."""
    q1 = recon_data["q1_increment_accounting"]
    assert q1["step1_converged_increments"] == 50
    assert q1["step2_converged_increments"] == 291
    assert q1["total_converged_increments"] == 341
    assert q1["energy_csv_data_rows"] == 341
    assert q1["total_attempted_increments"] == 342
    assert q1["step2_terminal_attempted_increment"] == 292
    assert q1["step2_terminal_cutback_attempts_count"] == 6
    assert q1["last_converged_step"] == 2
    assert q1["last_converged_increment"] == 291
    assert abs(q1["last_converged_disp_uy_mm"] - 0.00998) < 1e-4
    assert "reconciliation_explanation" in q1


def test_q2_fracture_energy_reconciliation(recon_data):
    """Q2: Verify -8.92% fracture energy discrepancy is bounded within <= 10.0% tolerance."""
    q2 = recon_data["q2_fracture_energy_reconciliation"]
    assert abs(q2["candidate_e10_terminal_df_mJ"] - 2.7274) < 1e-3
    assert abs(q2["baseline_f1685_terminal_df_mJ"] - 2.9946) < 1e-3
    assert abs(q2["relative_difference_pct"] - (-8.92)) < 0.1
    assert abs(q2["relative_difference_pct"]) <= 10.0
    assert q2["theoretical_sharp_surface_energy_mJ"] == 1.431
    assert "PASS" in q2["tolerance_status"]
    assert "physical_mechanism" in q2


def test_q3_post_severance_exit_mechanics(recon_data):
    """Q3: Verify Exit 1 is an unconstrained rigid-body artifact with 100% active fracture resolved."""
    q3 = recon_data["q3_solver_mechanics_and_exit_diagnosis"]
    assert q3["terminal_exit_code"] == 1
    assert q3["terminal_increment"] == 292
    assert q3["terminal_step"] == 2
    assert q3["terminal_cutbacks_exhausted"] == 6
    
    state = q3["physical_state_at_failure"]
    assert state["active_fracture_process_resolved_pct"] == 100.0
    assert state["post_severance_increments_solved_prior_to_exit"] == 131
    assert state["load_carrying_capacity_loss_pct"] > 99.7
    assert state["terminal_reaction_force_N"] < 2.0
    assert state["elastic_relaxation_pct"] > 99.6
    assert "root_cause_diagnosis" in q3


def test_q5_matched_speedup_comparison(recon_data):
    """Q5: Verify speedup is qualified at both matched physical states and full-job level."""
    q5 = recon_data["q5_matched_speedup_comparison"]
    
    # Milestone 1: complete severance
    sev = q5["matched_milestone_severance"]
    assert sev["speedup_at_severance"] >= 2.0
    assert abs(sev["speedup_at_severance"] - 2.55) < 0.1
    
    # Milestone 2: matched terminal displacement
    term = q5["matched_milestone_terminal_uy"]
    assert term["matched_endpoint_cpu_speedup"] >= 2.0
    assert term["matched_endpoint_walltime_speedup"] >= 1.8
    assert abs(term["matched_endpoint_cpu_speedup"] - 2.05) < 0.1
    assert abs(term["matched_endpoint_walltime_speedup"] - 1.88) < 0.1
    
    # Full-job comparison
    full = q5["full_job_comparison"]
    assert full["full_job_cpu_speedup"] >= 2.5
    assert full["full_job_walltime_speedup"] >= 2.3
    assert abs(full["full_job_cpu_speedup"] - 2.74) < 0.1
    assert abs(full["full_job_walltime_speedup"] - 2.50) < 0.1


def test_q6_fracture_timeline_and_mechanical_parity(recon_data):
    """Q6: Verify physical fracture milestones and strict mechanical parity."""
    timeline = recon_data["q2_q3_fracture_timeline"]
    
    # Primary peak
    p1 = timeline["milestone_1_primary_peak"]
    assert abs(p1["reaction_force_kN"] - 0.5597) < 1e-3
    assert abs(p1["disp_uy_mm"] - 0.00536) < 1e-4
    
    # Hole arrest
    p2 = timeline["milestone_2_hole_arrest"]
    assert p2["step"] == 2
    assert abs(p2["fracture_energy_mJ"] - 0.4575) < 1e-2
    assert 0.0058 <= p2["disp_uy_mm"] <= 0.0062
    
    # Secondary peak
    p3 = timeline["milestone_3_secondary_peak"]
    assert abs(p3["reaction_force_kN"] - 0.4980) < 1e-3
    assert abs(p3["disp_uy_mm"] - 0.00764) < 1e-4
    
    # Severance
    p4 = timeline["milestone_4_complete_ligament_severance"]
    assert p4["step"] == 2
    assert p4["inc"] == 160
    assert abs(p4["fracture_energy_mJ"] - 2.7237) < 1e-2
    assert p4["elastic_relaxation_pct"] > 99.5
    
    # Terminal converged state
    p5 = timeline["milestone_5_terminal_converged_state"]
    assert p5["step"] == 2
    assert p5["inc"] == 291
    assert abs(p5["disp_uy_mm"] - 0.00998) < 1e-4
    assert p5["load_drop_pct"] > 99.7


def test_q4_reporting_boundaries_and_verdict(recon_data):
    """Q4: Verify explicit disclosure of reporting boundaries and scientific verdict."""
    boundaries = recon_data["q4_q6_reporting_boundaries"]
    assert len(boundaries["verified_quantities"]) >= 10
    assert len(boundaries["reporting_boundaries_and_unverified_quantities"]) >= 3
    
    verdict = recon_data["scientific_qualification_verdict"]
    assert verdict == "PHYSICAL_FRACTURE_QUALIFIED_WITH_POST_SEVERANCE_CUTBACK_LIMITATION"
    assert "APPROVE" in recon_data["recommendation"]
