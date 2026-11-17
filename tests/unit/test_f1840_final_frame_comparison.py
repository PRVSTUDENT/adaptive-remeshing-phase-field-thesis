# -*- coding: utf-8 -*-
"""
tests/unit/test_f1840_final_frame_comparison.py
===============================================
Unit test suite verifying Task F1840:
Final-Frame Remesh and Comparison for Case 2 Paper-Reproduction Reference.
"""
import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_baselines_integrity():
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    expected_uel = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert sha256_file(uel_path) == expected_uel, "Frozen UEL hash corrupted!"

    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    expected_framework = "B0857C521AE8E212C74F711CC3373AD57B081167727104905A0F4D2FBBDA0129"
    assert sha256_file(framework_path) == expected_framework, "Shared framework hash corrupted!"

def test_pbs_accounting_and_governance():
    task_json_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json_path, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["task_id"] in [
        "F1840-CASE2-FINAL-FRAME-REMESH-COMPARISON",
        "F1841-F1840-ARTIFACT-TABLE-CORRECTION",
        "F1842-F1840-FINAL-REPORT-CORRECTION"
    ]
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 36
    assert task["master_goal_status"] == "OPEN"

def test_donor_odb_integrity_and_fidelity():
    donor_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "PK_F1840_CASE2_FINAL_FRAME_DONOR.odb")
    assert os.path.exists(donor_path), "Missing donor ODB!"
    assert os.path.getsize(donor_path) == 7526008
    assert sha256_file(donor_path) == "A48C17D793077BD08D9B95177CFFB9F7C4FA39ED1E6959A37F20CD515FBA27A5"

    fidelity_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "f1840_extraction_fidelity_audit.json")
    assert os.path.exists(fidelity_path), "Missing fidelity audit JSON!"
    with open(fidelity_path, "r") as f:
        audit = json.load(f)

    assert audit["source_frame_idx"] == 337
    assert audit["field_fidelity"]["exact_match"] is True
    assert audit["field_fidelity"]["max_abs_diff_miseseri"] == 0.0
    assert audit["field_fidelity"]["max_abs_diff_misesavg"] == 0.0
    assert audit["field_fidelity"]["max_abs_diff_sdv1"] == 0.0
    assert abs(audit["field_metrics"]["physical_eri_max_mpa"] - 986.18) < 0.1
    assert abs(audit["field_metrics"]["physical_avg_max_mpa"] - 2775.76) < 0.1

def test_case2_final_frame_quality_gates():
    receipt_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "PK_F1840_CASE2_FINAL_FRAME_REMESH_RECEIPT.json")
    assert os.path.exists(receipt_path), "Missing remesh receipt!"
    with open(receipt_path, "r") as f:
        rcp = json.load(f)

    assert rcp["adapted_mesh_body_sha256"] == "26FBE77367FB71EE2DE300A2E7B9B7EC26E82E0FF333BC37F807A1BE0F647AC6"

    audit = rcp["audit_metrics"]

    # Gate 01: Positive Jacobians
    assert audit["min_det_j"] > 0
    assert audit["non_positive_jacobians"] == 0
    assert audit["jacobian_status"] == "PASS"

    # Gate 02: Quad fraction >= 85%
    assert audit["quad_fraction_pct"] >= 85.0
    assert audit["quad_fraction_pct"] > 97.0  # Measured 97.76%

    # Gate 03: Max AR < 4.0
    assert audit["max_aspect_ratio"] < 4.0  # Measured 2.21

    # Gate 06: Plainly reported as FAIL
    assert audit["refinement_ratio_far_to_core"] < 2.0  # Measured 1.8043x
    assert audit["refinement_ratio_far_to_core"] > 1.70

    # Gate 07: Element budget < 80,000 and < 30,000
    assert audit["total_elements"] < 80000
    assert audit["total_elements"] < 30000
    assert audit["total_elements"] == 28160

    # Provenance
    assert audit["provenance_classification"] == "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR"

def test_distal_ligament_resolution_and_coverage():
    receipt_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "PK_F1840_CASE2_FINAL_FRAME_REMESH_RECEIPT.json")
    with open(receipt_path, "r") as f:
        rcp = json.load(f)

    spatial = rcp["spatial_breakdown"]
    distal_rep = spatial["distal_report_window"]
    distal_f1812 = spatial["distal_f1812_window"]

    # Report window coverage
    assert distal_rep["cov_le_l0_pct"] == 100.0
    assert distal_rep["cov_le_half_l0_pct"] >= 90.0  # Measured 91.48%
    assert distal_rep["count"] == 8759

    # F1812 window coverage
    assert distal_f1812["cov_le_l0_pct"] >= 99.0  # Measured 99.75%
    assert distal_f1812["cov_le_half_l0_pct"] >= 90.0  # Measured 91.35%
    assert distal_f1812["count"] == 9052

def test_comparison_metrics_with_frame_300():
    receipt_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "PK_F1840_CASE2_FINAL_FRAME_REMESH_RECEIPT.json")
    with open(receipt_path, "r") as f:
        rcp = json.load(f)

    comp = rcp["comparison_with_frame_300"]
    # Delta elements is virtually zero (-5 elements)
    assert abs(comp["elements"]["delta_pct"]) < 0.1
    assert comp["elements"]["final_frame"] == 28160
    assert comp["elements"]["f300"] == 28165

    # Gate 06 improved slightly (1.7325 -> 1.8043)
    assert comp["gate_06_coarsening"]["final_frame"] > comp["gate_06_coarsening"]["f300"]

    # Max AR improved (2.60 -> 2.21)
    assert comp["max_aspect_ratio"]["final_frame"] < comp["max_aspect_ratio"]["f300"]


def test_visualization_figures_existence():
    fig_dir = os.path.join(REPO_ROOT, "results", "figures")
    png_final = os.path.join(fig_dir, "fig_f1840_case2_final_frame_mesh.png")
    pdf_final = os.path.join(fig_dir, "fig_f1840_case2_final_frame_mesh.pdf")
    png_comp = os.path.join(fig_dir, "fig_f1840_case2_comparison.png")
    pdf_comp = os.path.join(fig_dir, "fig_f1840_case2_comparison.pdf")

    assert os.path.exists(png_final), "Final frame PNG missing"
    assert os.path.exists(pdf_final), "Final frame PDF missing"
    assert os.path.exists(png_comp), "Comparison PNG missing"
    assert os.path.exists(pdf_comp), "Comparison PDF missing"

    assert os.path.getsize(png_final) > 1000000
    assert os.path.getsize(pdf_final) > 1000000
    assert os.path.getsize(png_comp) > 1000000
    assert os.path.getsize(pdf_comp) > 1000000

def test_report_existence_and_artifact_table_reconciliation():
    rep_path = os.path.join(REPO_ROOT, "docs", "validation", "F1840_CASE2_FINAL_FRAME_REMESH_COMPARISON_REPORT.md")
    assert os.path.exists(rep_path), "F1840 report missing!"
    assert os.path.getsize(rep_path) > 10000
    with open(rep_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "458e6a9d8cb36fae18f357e11577989adac4617e" in content
    assert "26FBE77367FB71EE2DE300A2E7B9B7EC26E82E0FF333BC37F807A1BE0F647AC6" in content
    assert "986.18" in content

def test_remesh_script_body_sha_reproduction():
    from scripts.remeshing.run_f1840_case2_final_frame_remesh import compute_body_sha256
    mesh_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "PK_F1840_CASE_2_FINAL_FRAME_PHYS.inp")
    computed_sha = compute_body_sha256(mesh_path)
    assert computed_sha == "26FBE77367FB71EE2DE300A2E7B9B7EC26E82E0FF333BC37F807A1BE0F647AC6"
