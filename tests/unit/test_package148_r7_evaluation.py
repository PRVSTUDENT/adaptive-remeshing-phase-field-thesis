"""
Unit tests verifying the scientific and numerical evaluation of Package 148 Revision 7 (Job 1418938.mmaster02).
"""
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_package148_r7_evaluation_artifact():
    eval_path = REPO_ROOT / "results" / "validation" / "package148" / "r7_evaluation.json"
    assert eval_path.exists(), "r7_evaluation.json must exist"
    data = json.loads(eval_path.read_text())
    assert data["schema"] == 1
    assert data["pbs_job_id"] == "1418938.mmaster02"
    assert data["terminal_status"] == "FAILED"
    assert data["exit_code"] == 1
    assert data["total_outer_iterations"] == 25

    traj = data["convergence_trajectory"]
    assert traj["delta_d_passed"] is True
    assert traj["delta_u_passed"] is True
    assert traj["dual_error_final"] == 0.0

    gates = data["stage_c1_physical_gates"]
    assert gates["rf2_gate_pass"] is True
    assert gates["delta_rf2_relative"] < 0.01  # less than 1%
    assert gates["energy_gate_pass"] is True
    assert gates["delta_energy_relative"] < 0.005  # less than 0.5%
    assert gates["damage_bound_pass"] is True
    assert gates["all_physical_gates_pass"] is True
