"""
test_mode1_f1597_package120_convergence_diagnosis.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 120 15-cycle alternating minimization convergence diagnosis:
1. Verifies existence and schema of results/validation/package120_convergence_diagnosis.json.
2. Asserts extraction of all 15 AM cycles with unrounded metrics.
3. Asserts contraction factor minimum at Cycle 12 (Delta d = 0.006913, Delta RF2 = 0.4198 N).
4. Asserts contraction factor reversal at Cycles 13-15 (rho_d > 1.0 and rho_F > 1.0).
5. Asserts active-set recruitment (+62 free nodes between Cycle 3 and Cycle 15).
6. Asserts refutation of Hypothesis H1 (insufficient iteration budget) and rejection of R1 retry.
7. Asserts failure mode classification: ACTIVE_CRACK_SOFTENING_INSTABILITY_UNDER_FIXED_DISPLACEMENT.
8. Asserts scientific status: HOLDOUT_NONSTATIONARY_UNRESOLVED.
9. Asserts binding governance: Gate C1-2 Step 2 remains strictly C1_2_STEP2_ENERGY_GATE_FAILED.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

@pytest.fixture(scope="module")
def diag_data():
    path = os.path.join(REPO_ROOT, "results/validation/package120_convergence_diagnosis.json")
    assert os.path.exists(path), f"Missing diagnosis artifact: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_diagnosis_schema_and_task(diag_data):
    assert diag_data["schema"] == 1
    assert diag_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert "predecessor_result" in diag_data
    assert diag_data["predecessor_result"]["scientific_status"] == "HOLDOUT_NONSTATIONARY_UNRESOLVED"

def test_cycle_history_completeness(diag_data):
    history = diag_data["cycle_history_audit"]
    assert len(history) == 15
    for i, cyc in enumerate(history, start=1):
        assert cyc["cycle"] == i
        assert cyc["rf2_rp_N"] > 175.0
        assert cyc["d_max"] > 0.50
        assert cyc["e_tot_mJ"] > 0.23

def test_contraction_minimum_and_reversal(diag_data):
    analysis = diag_data["contraction_factor_analysis"]
    c_min = analysis["contraction_minimum"]
    assert c_min["cycle"] == 12
    assert pytest.approx(c_min["d_max"], rel=1e-3) == 0.70910
    assert pytest.approx(c_min["delta_d_max"], rel=1e-3) == 0.006913

    reversal = analysis["contraction_reversal"]
    assert reversal["reversal_detected_at_cycle"] == 13
    tail_rho_d = reversal["tail_rho_d"]
    tail_rho_F = reversal["tail_rho_rf2"]

    assert len(tail_rho_d) == 3
    assert len(tail_rho_F) == 3

    # All tail contraction factors must exceed 1.0 (divergence / expanding increments)
    for rho in tail_rho_d:
        assert rho > 1.0, f"Expected expanding damage increment (rho_d > 1.0), got {rho}"
    for rho in tail_rho_F:
        assert rho > 1.0, f"Expected expanding force drift (rho_F > 1.0), got {rho}"

def test_active_set_recruitment(diag_data):
    rec = diag_data["active_set_recruitment_audit"]
    assert rec["free_nodes_cycle_3"] == 4276
    assert rec["free_nodes_cycle_15"] == 4338
    assert rec["recruited_active_nodes"] == 62

def test_hypothesis_h1_refutation_and_no_submission(diag_data):
    h1 = diag_data["hypothesis_h1_evaluation"]
    assert h1["evaluation_result"] == "REFUTED"
    assert h1["r1_experiment_justified"] is False
    assert h1["r1_submission_decision"] == "NO_SUBMISSION_UNSUPPORTED_RETRY"
    assert diag_data["failure_mode_classification"] == "ACTIVE_CRACK_SOFTENING_INSTABILITY_UNDER_FIXED_DISPLACEMENT"

def test_governance_retained(diag_data):
    gov = diag_data["governance_status"]
    assert "C1_2_STEP2_ENERGY_GATE_FAILED" in gov["original_gate_status"]
    assert gov["c5_remeshing_permitted"] is False
