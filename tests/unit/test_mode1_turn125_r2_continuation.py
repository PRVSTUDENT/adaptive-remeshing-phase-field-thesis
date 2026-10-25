"""
test_mode1_turn125_r2_continuation.py
Unit tests for Mode-I Task F1597 Turn 125 Package 108 Revision 2 Staggered Continuation.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_turn125_r2_reconciliation_metrics():
    recon_path = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn125_c3_staggered_r2_reconciliation.json"
    assert recon_path.exists(), "Reconciliation artifact does not exist"
    with open(recon_path, "r") as f:
        data = json.load(f)

    assert data["job_id"] == "1417251.mmaster02"
    assert data["terminal_state"] == "F"
    assert data["exit_code"] == 0
    assert data["solver_completion"] == "THE ANALYSIS HAS COMPLETED SUCCESSFULLY"
    assert data["overall_continuation_verdict"] == "GENUINE_STAGGERED_CONTINUATION_SUCCESS"

    # Stage A checks
    stage_a = data["stage_a_evaluation"]
    assert stage_a["status"] == "PASS"
    assert stage_a["relative_error_pct"] < 0.1  # measured 0.00197%
    assert abs(stage_a["measured_ef_mJ"] - 0.0610158) < 1.0e-5

    # Stage B Mech checks
    mech = data["stage_b_mech_evaluation"]
    assert mech["status"] == "PASS"
    assert mech["equil_iters"] == 1
    assert mech["phase_holding_drift_mJ"] < 1.0e-9

    # Stage B Phase checks
    phase = data["stage_b_phase_evaluation"]
    assert phase["status"] == "PASS"
    assert phase["dissipation_positive"] is True
    assert phase["free_energy_decreasing"] is True
    assert phase["final_ef_mJ"] > stage_a["measured_ef_mJ"]
