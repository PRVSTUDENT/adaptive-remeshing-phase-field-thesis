"""Unit test suite for Method C Phase 2: Job-1 Baseline Solve Verification & Observables.
Verifies completion receipt, extracted field observables, solver zero-error status,
and baseline observables report integrity.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def test_job1_receipt_verification():
    receipt_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case", "PK_METHOD_C_DEMO_COARSE_JOB1_RECEIPT.json"
    )
    assert os.path.isfile(receipt_path), f"Receipt missing: {receipt_path}"

    with open(receipt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["job_id"] == "1424517.mmaster02"
    assert data["job_name"] == "PK_METHOD_C_DEMO_COARSE_JOB1"
    assert data["exit_code"] == 0
    assert data["status"] == "COMPLETED_EXIT0"
    assert data["solver_completed_cleanly"] is True
    assert data["step1_increments"] == 50
    assert data["step1_end_u2_mm"] == pytest.approx(0.0050, rel=1e-4)
    assert data["RF2_kN"] == pytest.approx(0.556024, rel=1e-3)
    assert data["peak_damage_SDV1"] == pytest.approx(0.169178, rel=1e-3)
    assert data["mean_damage_SDV1"] == pytest.approx(0.008609, rel=1e-2)
    assert data["bulk_damage_intact_verified"] is True
    assert data["peak_history_SDV2_MPa"] == pytest.approx(0.249872, rel=1e-3)
    assert data["peak_miseseri"] == 0.0
    assert data["elements_count"] == 8760
    assert data["nodes_count"] == 3017


def test_job1_summary_json():
    summary_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case", "PK_METHOD_C_DEMO_COARSE_JOB1_SUMMARY.json"
    )
    assert os.path.isfile(summary_path), f"Summary missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["exit_code"] == 0
    assert data["sta_completed_successfully"] is True
    assert data["msg_zero_errors"] is True
    assert data["max_damage"] == pytest.approx(0.169178, rel=1e-3)
    assert data["max_history_MPa"] == pytest.approx(0.249872, rel=1e-3)
    assert data["RF2_kN"] == pytest.approx(0.556024, rel=1e-3)
    assert data["max_miseseri"] == 0.0


def test_job1_report_integrity():
    report_path = os.path.join(
        REPO_ROOT, "docs", "validation", "METHOD_C_PHASE2_JOB1_BASELINE_OBSERVABLES_REPORT.md"
    )
    assert os.path.isfile(report_path), f"Report missing: {report_path}"

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1424517.mmaster02" in content
    assert "Exit Code 0" in content
    assert "0.556024" in content
    assert "0.169178" in content
    assert "0.249872" in content
    assert "MISESERI" in content
    assert "8,760" in content
