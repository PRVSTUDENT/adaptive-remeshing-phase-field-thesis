# -*- coding: utf-8 -*-
"""
test_method_c_cycle2_job4_execution.py
======================================
Unit tests for Method C Cycle 2 Job-4 re-equilibration and forward propagation execution:
- Verifies PK_METHOD_C_CYCLE2_REFINED_JOB4_RECEIPT.json
- Verifies PK_METHOD_C_CYCLE2_REFINED_JOB4_SUMMARY.json
- Verifies docs/validation/METHOD_C_CYCLE2_JOB4_EXECUTION_REPORT.md
- Verifies HPC_JOB_LEDGER.csv and cumulative PBS job accounting
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CYCLE2_JOB4_EXECUTION_REPORT.md")
RECEIPT_PATH = os.path.join(CASE_DIR, "PK_METHOD_C_CYCLE2_REFINED_JOB4_RECEIPT.json")
SUMMARY_PATH = os.path.join(CASE_DIR, "PK_METHOD_C_CYCLE2_REFINED_JOB4_SUMMARY.json")
HPC_LEDGER_PATH = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")


def test_job4_receipt_verification():
    assert os.path.isfile(RECEIPT_PATH), "Job-4 receipt JSON missing: %s" % RECEIPT_PATH
    with open(RECEIPT_PATH, "r") as f:
        receipt = json.load(f)

    assert receipt["job_id"] == "1424702.mmaster02"
    assert receipt["job_name"] == "PK_METHOD_C_CYCLE2_REFINED_JOB4"
    assert receipt["status"] == "CUTBACK_TERMINATION"
    assert receipt["exit_code"] == 1
    assert receipt["termination_reason"] == "TIME_INCREMENT_LESS_THAN_MINIMUM"
    assert receipt["physical_elements_count"] == 14004
    assert receipt["layered_elements_count"] == 42012
    assert receipt["step1_increments"] == 6
    assert receipt["step1_init_force_continuity_pass"] is True
    assert receipt["step1_init_RF2_kN"] == pytest.approx(0.249323, abs=1e-4)
    assert receipt["step1_init_force_continuity_delta_pct"] == pytest.approx(-4.92068, abs=1e-2)
    assert receipt["peak_history_SDV2_MPa"] == pytest.approx(4629.688965, abs=1e-3)
    assert receipt["peak_damage_SDV1"] >= 1.0
    assert receipt["final_crack_tip_x_mm"] == pytest.approx(0.923302, abs=1e-4)
    assert receipt["final_crack_extension_mm"] == pytest.approx(0.423302, abs=1e-4)
    assert receipt["peak_RF2_kN"] == pytest.approx(0.249323, abs=1e-4)
    assert receipt["E_fracture_kNmm"] == pytest.approx(0.001686, abs=1e-4)


def test_job4_summary_integrity():
    assert os.path.isfile(SUMMARY_PATH), "Job-4 summary JSON missing: %s" % SUMMARY_PATH
    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    assert summary["job_id"] == "1424702.mmaster02"
    assert summary["total_increments"] == 6
    assert summary["total_cutbacks"] == 8
    assert summary["total_equilibrium_iterations"] == 63
    assert summary["walltime_s"] == pytest.approx(74.0, abs=5.0)
    assert summary["cpu_time_s"] == pytest.approx(204.0, abs=5.0)
    assert len(summary["dat_rp_history"]) == 6
    assert summary["initial_crack_tip_x_mm"] == pytest.approx(0.895686, abs=1e-4)
    assert summary["final_crack_tip_x_mm"] == pytest.approx(0.923302, abs=1e-4)
    assert summary["final_crack_tip_x_mm"] > summary["initial_crack_tip_x_mm"]
    assert summary["step1_init_force_continuity_pass"] is True
    assert summary["step1_init_force_continuity_delta_pct"] == pytest.approx(-4.92068, abs=1e-2)


def test_job4_execution_report_integrity():
    assert os.path.isfile(REPORT_PATH), "Job-4 execution report missing: %s" % REPORT_PATH
    with open(REPORT_PATH, "r") as f:
        content = f.read()

    assert "METHOD-C-CYCLE2-JOB4-SOLVE" in content
    assert "1424702.mmaster02" in content
    assert "PK_METHOD_C_CYCLE2_REFINED_JOB4.inp" in content
    assert "3A9F32BA" in content or "3a9f32ba" in content.lower()
    assert "CE8D5EDC" in content
    assert "0.923302" in content
    assert "0.249323" in content
    assert "4629.688965" in content
    assert "CUTBACK_TERMINATION" in content


def test_job4_provenance_and_accounting():
    assert os.path.isfile(HPC_LEDGER_PATH), "HPC job ledger missing"
    with open(HPC_LEDGER_PATH, "r") as f:
        lines = f.readlines()

    job4_lines = [l for l in lines if "1424702.mmaster02" in l]
    assert len(job4_lines) == 1
    l = job4_lines[0]
    assert "demo_cycle2_job4" in l
    assert "COMPLETED" in l
    assert "3a9f32baeb5d1f4d810f60872897c443558e61569cfb1b58c60dd9fb24f5e688" in l
