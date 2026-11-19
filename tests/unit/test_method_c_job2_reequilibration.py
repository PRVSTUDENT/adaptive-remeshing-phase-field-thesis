"""Unit test suite for Method C Phase 2: Job-2 Re-Equilibration Solve Verification & Continuity.
Verifies completion receipt, extracted observables, reaction force continuity (RF2),
energy balance continuity (E_total), damage irreversibility (no healing), and report integrity.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def test_job2_receipt_verification():
    receipt_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case", "PK_METHOD_C_DEMO_REFINED_STEP1_JOB2_RECEIPT.json"
    )
    assert os.path.isfile(receipt_path), f"Receipt missing: {receipt_path}"

    with open(receipt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["job_id"] == "1424584.mmaster02"
    assert data["job_name"] == "PK_METHOD_C_DEMO_REFINED_STEP1_JOB2"
    assert data["exit_code"] == 0
    assert data["status"] == "COMPLETED_EXIT0"
    assert data["solver_completed_cleanly"] is True
    assert data["total_increments"] == 24
    assert data["total_cutbacks"] == 0
    assert data["total_equilibrium_iterations"] == 66
    assert data["end_u2_mm"] == pytest.approx(0.0050, rel=1e-4)
    assert data["RF2_kN"] == pytest.approx(0.548386, rel=1e-3)
    assert data["baseline_RF2_kN"] == pytest.approx(0.556024, rel=1e-3)
    assert data["delta_RF2_percent"] == pytest.approx(-1.3737, rel=1e-2)
    assert abs(data["delta_RF2_percent"]) < 5.0
    assert data["E_total_kNmm"] == pytest.approx(0.00141244, rel=1e-3)
    assert data["baseline_E_total_kNmm"] == pytest.approx(0.00142340, rel=1e-3)
    assert data["delta_E_total_percent"] == pytest.approx(-0.7696, rel=1e-2)
    assert abs(data["delta_E_total_percent"]) < 5.0
    assert data["damage_healing_strictly_prevented"] is True
    assert data["peak_damage_SDV1"] >= 0.169178
    assert data["history_non_negative_verified"] is True
    assert data["physical_elements_count"] == 10299
    assert data["layered_elements_count"] == 30897
    assert data["nodes_count"] == 10299


def test_job2_summary_json():
    summary_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case", "PK_METHOD_C_DEMO_REFINED_STEP1_JOB2_SUMMARY.json"
    )
    assert os.path.isfile(summary_path), f"Summary missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["exit_code"] == 0
    assert data["sta_completed_successfully"] is True
    assert data["msg_zero_errors"] is True
    assert data["max_damage"] >= 0.169178
    assert data["min_damage"] >= 0.0
    assert data["max_history_MPa"] > 0.0
    assert data["min_history_MPa"] >= -1e-12
    assert data["RF2_kN"] == pytest.approx(0.548386, rel=1e-3)
    assert data["E_total_kNmm"] == pytest.approx(0.00141244, rel=1e-3)
    assert data["walltime_s"] == pytest.approx(41.0, rel=1e-2)
    assert data["cpu_time_s"] == pytest.approx(175.0, rel=1e-2)


def test_job2_report_integrity():
    report_path = os.path.join(
        REPO_ROOT, "docs", "validation", "METHOD_C_PHASE2_JOB2_REEQUILIBRATION_REPORT.md"
    )
    assert os.path.isfile(report_path), f"Report missing: {report_path}"

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1424584.mmaster02" in content
    assert "Exit 0" in content
    assert "0.548386" in content
    assert "-1.37" in content
    assert "-0.77" in content
    assert "0.408571" in content
    assert "10,299" in content
    assert "30,897" in content
    assert "NOTE-MC-RQ-01" in content
