"""Unit test suite for Method C Phase 3: Step-2 Forward Crack Propagation Package on Refined Mesh.
Verifies Job-3 continuation deck generation, multi-step loading schedule (Step-1 re-equilibration,
Step-2 forward propagation to u2=0.0100 mm), initial state preservation, authorization manifest,
crack propagation path towards central hole, and package report integrity.
"""
import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
sys.path.insert(0, CASE_DIR)

import build_demo_propagation_job3_deck


def test_job3_deck_generation_and_integrity():
    deck_path, deck_sha, file_size = build_demo_propagation_job3_deck.build_job3_deck()
    assert os.path.isfile(deck_path), f"Job-3 deck missing: {deck_path}"
    assert file_size > 4000000, f"Deck file size too small: {file_size}"
    assert len(deck_sha) == 64

    with open(deck_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Model and heading assertions
    assert "PK_METHOD_C_DEMO_PROPAGATION_JOB3" in content
    assert "Step-2 Forward Crack Propagation" in content

    # 3-Layer element assertions
    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "*USER ELEMENT, TYPE=U3" in content
    assert "*USER ELEMENT, TYPE=U4" in content
    assert "*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS" in content
    assert "*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS" in content

    # Initial conditions
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content
    # Ensure TYPE=DISPLACEMENT is NOT present (prevents Fatal Error 144)
    assert "*INITIAL CONDITIONS, TYPE=DISPLACEMENT" not in content

    # Step 1: Re-equilibration at u2 = 0.0050 mm
    assert "*STEP, NAME=Step-1-ReEquilibrate" in content
    assert "N_RP, 2, 2, 0.0050" in content

    # Step 2: Forward crack propagation to u2 = 0.0100 mm
    assert "*STEP, NAME=Step-2-Propagate" in content
    assert "*BOUNDARY, OP=MOD" in content
    assert "N_RP, 2, 2, 0.0100" in content
    assert "0.10, 1.0, 1.0E-08, 0.20" in content


def test_job3_manifest_and_authorization():
    manifest_path = os.path.join(CASE_DIR, "METHOD_C_DEMO_JOB3_AUTHORIZATION.json")
    assert os.path.isfile(manifest_path), f"Manifest missing: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["task_id"] == "METHOD-C-PHASE3-FORWARD-PROPAGATION-PACKAGE"
    assert manifest["max_new_pbs_submissions"] in (0, 1)
    assert manifest["cumulative_pbs_submissions"] in (59, 60)
    assert manifest["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert manifest["resource_limits"]["ncpus"] == 16
    assert manifest["resource_limits"]["mem_gb"] == 48


def test_job3_package_report_integrity():
    report_path = os.path.join(
        REPO_ROOT, "docs", "validation", "METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md"
    )
    assert os.path.isfile(report_path), f"Report missing: {report_path}"

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PK_METHOD_C_DEMO_PROPAGATION_JOB3" in content
    assert "0.0050" in content
    assert "0.0100" in content
    assert "0.75" in content
    assert "NOTE-MC-J2-01" in content
    assert "530a0abb" in content
    assert "E75B82FC" in content
    assert "10,299" in content
    assert "30,897" in content


def test_job3_execution_receipt_and_observables():
    receipt_path = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_PROPAGATION_JOB3_RECEIPT.json")
    assert os.path.isfile(receipt_path), f"Receipt missing: {receipt_path}"

    with open(receipt_path, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    assert receipt["job_id"] == "1424609.mmaster02"
    assert receipt["job_name"] == "PK_METHOD_C_DEMO_PROPAGATION_JOB3"
    assert receipt["exit_code"] == 1
    assert receipt["status"] == "CUTBACK_TERMINATION_AT_HOLE_CAPTURE"
    assert receipt["termination_reason"] == "TIME_INCREMENT_LESS_THAN_MINIMUM"
    assert receipt["solver_completed_cleanly"] is False
    assert receipt["hole_reached"] is True
    assert receipt["post_peak_softening_demonstrated"] is True

    # Geometry & Discretization
    assert receipt["physical_elements_count"] == 10299
    assert receipt["layered_elements_count"] == 30897

    # Multi-step increments
    assert receipt["step1_increments"] == 24
    assert receipt["step2_increments"] == 125

    # Step-1 continuity with Job 2
    assert abs(receipt["step1_end_RF2_kN"] - 0.548386) < 1e-4

    # Peak load and post-peak softening
    assert receipt["peak_RF2_kN"] > 0.60
    assert abs(receipt["peak_RF2_kN"] - 0.648681) < 1e-3
    assert abs(receipt["u2_at_peak_RF2_mm"] - 0.006117) < 1e-4
    assert receipt["step2_end_RF2_kN"] < receipt["peak_RF2_kN"] * 0.50

    # Crack propagation and hole capture
    assert receipt["peak_damage_SDV1"] > 1.0
    assert receipt["final_crack_tip_x_mm"] >= 0.65
    assert receipt["final_crack_extension_mm"] >= 0.15

    # Energetics
    assert receipt["E_fracture_kNmm"] > 0.0010
    assert receipt["E_total_kNmm"] > 0.0020


def test_job3_summary_json_integrity():
    summary_path = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_PROPAGATION_JOB3_SUMMARY.json")
    assert os.path.isfile(summary_path), f"Summary missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["job_id"] == "1424609.mmaster02"
    assert summary["total_increments"] == 149
    assert summary["step1_increments"] == 24
    assert summary["step2_increments"] == 125
    assert summary["total_equilibrium_iterations"] == 713
    assert summary["hole_reached"] is True
    assert len(summary["crack_extension_history"]) == 126  # Frame 0 to 125


def test_job3_execution_report_integrity():
    report_path = os.path.join(
        REPO_ROOT, "docs", "validation", "METHOD_C_PHASE3_FORWARD_PROPAGATION_EXECUTION_REPORT.md"
    )
    assert os.path.isfile(report_path), f"Execution report missing: {report_path}"

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1424609.mmaster02" in content
    assert "CUTBACK_TERMINATION_AT_HOLE_CAPTURE" in content
    assert "TIME_INCREMENT_LESS_THAN_MINIMUM" in content
    assert "0.648681" in content
    assert "0.548386" in content
    assert "0.65" in content
    assert "0.895686" in content
    assert "0.395686" in content
    assert "1.005501" in content
    assert "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6" in content
