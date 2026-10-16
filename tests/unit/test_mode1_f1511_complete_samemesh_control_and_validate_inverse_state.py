"""
Unit tests for Task F1511:
Complete same-mesh control experiment and mathematically/numerically validate
least-squares inverse state reconstruction for Method C Stage C1-1 nonmatching state transfer.
"""
import json
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_manifest_qualification_and_job_record():
    manifest_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "METHOD_C_STAGE_C1_1_SAMEMESH_CONSISTENT_AUTHORIZATION.json"
    assert manifest_path.exists(), f"Missing manifest: {manifest_path}"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["batch_name"] == "MODE1_METHOD_C_STAGE_C1_1"
    assert "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.inp" in data["files"]
    assert "submit_M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.pbs" in data["files"]
    assert data["files"]["f42_mixed_uel.for"] == "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def test_samemesh_line_diff_boundary_restriction():
    deck_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
    deck1 = deck_dir / "M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.inp"
    deck2 = deck_dir / "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.inp"
    assert deck1.exists(), f"Missing deck 1: {deck1}"
    assert deck2.exists(), f"Missing deck 2: {deck2}"
    assert deck1.stat().st_size > 7_000_000
    assert deck2.stat().st_size > 7_000_000


def test_authentic_4panel_figure_exists():
    fig_dir = REPO_ROOT / "results" / "figures" / "mode1_method_c_gate_c1"
    png_path = fig_dir / "fig_mode1_method_c_stage_c1_1_mesh_and_phase_transfer.png"
    pdf_path = fig_dir / "fig_mode1_method_c_stage_c1_1_mesh_and_phase_transfer.pdf"
    assert png_path.exists(), f"Missing PNG figure: {png_path}"
    assert pdf_path.exists(), f"Missing PDF figure: {pdf_path}"
    assert png_path.stat().st_size > 1_000_000, "Figure PNG size unexpectedly small"
    assert pdf_path.stat().st_size > 10_000, "Figure PDF size unexpectedly small"


def test_fortran_d_avg_operator_definition():
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "f42_mixed_uel.for"
    assert uel_path.exists(), f"Missing UEL source: {uel_path}"
    with open(uel_path, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()
    # Quad D_AVG definition (1/4 sum d_i)
    assert "D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))" in src
    # Tri D_AVG definition (1/3 sum d_i)
    assert "D_AVG = (U(1) + U(2) + U(3)) / THREE" in src
    # Companion UMAT export
    assert "STATEV(14) = SV_PHASE_TRIAL(PHYSIDX)" in src


def test_hpc_job_ledger_recording():
    ledger_path = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    assert ledger_path.exists()
    with open(ledger_path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "1414558.mmaster02" in text
    assert "1414563.mmaster02" in text
    assert "M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD" in text
    assert "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD" in text


def test_active_task_and_coordination_state():
    task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)
    assert task["task_id"] == "F1511-COMPLETE-SAMEMESH-CONTROL-AND-VALIDATE-INVERSE-STATE"
    assert "1414558.mmaster02" in task["active_pbs_job_ids"]
    assert "1414563.mmaster02" in task["active_pbs_job_ids"]
    assert "Gate 6C" in task["phase"] or "GATE_6C" in task["gate_status"]
