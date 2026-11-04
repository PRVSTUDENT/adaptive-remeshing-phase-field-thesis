#!/usr/bin/env python3
"""
Unit tests for Candidate Package 171-R8 Mathematical Specification Evaluation
Task: F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION
"""
import hashlib
import json
from pathlib import Path
import pytest

from scripts.validation.evaluate_mode1_r8_mathematical_specification import (
    evaluate_r8_specification,
    compute_sha256,
    FROZEN_UEL_SHA256,
)

WORKSPACE = Path(__file__).resolve().parent.parent.parent

def test_frozen_uel_sha256_preservation():
    uel_path = WORKSPACE / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    assert uel_path.exists(), f"UEL file missing: {uel_path}"
    uel_hash = compute_sha256(uel_path)
    assert uel_hash == FROZEN_UEL_SHA256, f"Frozen UEL hash altered: {uel_hash}"

def test_r8_specification_assessment_artifact():
    artifact_path = WORKSPACE / "results/validation/mode1_r8_mathematical_specification_assessment.json"
    assert artifact_path.exists(), f"Missing artifact: {artifact_path}"
    with open(artifact_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    assert result["schema"] == 1
    assert result["verification_passed"] is True
    assert result["status"] == "R8_MATHEMATICAL_SPECIFICATION_VERIFIED"
    assert len(result["finding"]) >= 20

    # Compound transition checks
    trans = result["compound_transition_specification"]
    assert trans["max_active_cardinality"] == 500
    assert trans["max_symmetric_diff"] == 10
    assert trans["max_added_nodes"] == 0
    assert trans["consecutive_iterations_required"] == 3
    assert trans["simulated_trigger_outer_iteration"] in [82, 89]

    # Trigger state sanity checks
    state = trans["simulated_trigger_state"]
    assert state["outer"] in [82, 89]
    active_cnt = state.get("active_count", state.get("pdas_active_count"))
    assert active_cnt <= 500
    sym_cnt = state.get("symmetric_diff", state.get("active_set_symmetric_diff"))
    assert sym_cnt <= 10
    added_cnt = state.get("added_nodes", state.get("added_nodes_count"))
    assert added_cnt == 0

    # Iteration budget & runtime feasibility checks
    ib = result["iteration_budget_qualification"]
    assert ib["proposed_max_outer"] == 140
    assert ib["trigger_iteration"] in [82, 89]
    assert ib["available_relaxation_iterations"] >= 50
    assert ib["estimated_iterations_required_to_converge"] == 40
    assert ib["estimated_total_iterations_to_convergence"] == 129

    # Prove that 120 iterations was insufficient (extrapolation delta_d > 1e-5)
    assert ib["convergence_feasible_within_120"] is False
    assert ib["projected_delta_d_at_iteration_120"] > 1.0e-5

    # Prove that 140 iterations is qualified and sufficient (projected delta_d <= 1e-5)
    assert ib["convergence_feasible_within_140"] is True
    assert ib["projected_delta_d_at_iteration_140"] <= 1.0e-5

    rf = result["runtime_feasibility"]
    assert rf["feasible"] is True
    assert rf["feasible_within_8h"] is True
    assert rf["projected_walltime_140_iters_h"] < 8.0
    assert rf["walltime_headroom_8h_pct"] > 75.0

    # Offline hypothesis disclaimer check
    assert "offline_telemetry_hypothesis_disclaimer" in result
    assert len(result["offline_telemetry_hypothesis_disclaimer"]) >= 50

    # Safeguards
    sg = result["safeguards_and_rollback"]
    assert sg["divergence_safeguard"]["factor_gamma"] == 1.5
    assert sg["divergence_safeguard"]["max_consecutive_divergence"] == 2
    assert sg["divergence_safeguard"]["action"] == "ROLLBACK_TO_CHECKPOINT_AND_RESTORE_STAGE1"
    assert sg["healing_safeguard"]["max_negative_delta_d"] == 1.0e-6

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
