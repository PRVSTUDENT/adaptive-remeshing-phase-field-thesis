import json
import pytest
from pathlib import Path

def test_r7_terminal_evidence_exists():
    ev_dir = Path("models/pandey_kumar_mode1/171_c6_package171_r7_c3_0_adaptive_reequilibration/evidence/1419873.mmaster02")
    assert (ev_dir / "live_iteration_telemetry.json").exists()
    assert (ev_dir / "re_equilibration_summary.json").exists()
    assert (ev_dir / "pbs_execution.log").exists()

def test_r7_terminal_accounting():
    eval_file = Path("results/validation/c6_r7_execution_reconciliation_and_acceptance.json")
    assert eval_file.exists()
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["pbs_job_id"] == "1419873.mmaster02"
    assert data["pbs_accounting"]["exit_status"] == 1
    assert data["outer_iterations_completed"] == 100
    assert data["classification"] == "NUMERICALLY_NONCONVERGED"
    assert data["scientific_acceptance"] == "FAIL_COUPLED_NONCONVERGENCE"
    assert data["accepted_c6_checkpoint"] == "NONE"

def test_r7_active_set_stabilization_failure():
    eval_file = Path("results/validation/c6_r7_execution_reconciliation_and_acceptance.json")
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    dynamics = data["active_set_dynamics"]
    assert dynamics["terminal_active_count"] == 160
    assert dynamics["terminal_symmetric_diff"] == 4
    assert dynamics["membership_stability_criterion_met"] is False
    assert data["safeguarded_relaxation_trajectory"]["stage_2_reached"] is False
    assert data["safeguarded_relaxation_trajectory"]["transition_count"] == 0
    assert data["safeguarded_relaxation_trajectory"]["rollback_count"] == 0

def test_r7_kkt_compliance():
    eval_file = Path("results/validation/c6_r7_execution_reconciliation_and_acceptance.json")
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    metrics = data["metrics"]
    assert metrics["kkt_free_passed"] is True
    assert metrics["kkt_dual_passed"] is True
    assert metrics["kkt_complementarity_passed"] is True
    assert metrics["last_kkt_free_error"] <= 1.0e-6
    assert metrics["last_kkt_dual_error"] <= 1.0e-6
