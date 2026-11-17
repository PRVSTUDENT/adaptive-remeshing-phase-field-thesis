# -*- coding: utf-8 -*-
"""
tests/unit/test_f1838_case2_native_pilot.py
===========================================
Task F1838: Bounded Native Job-1 Pilot for Case 2 & Case 1 Islands Diagnosis.
Verifies all mechanical equivalence, solver telemetry, single-frame native remesh
finite-element quality gates, provenance consistency, and governance integrity constraints.
"""
import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "277_f1838_case2_native_pilot")
RECEIPT_PATH = os.path.join(OUT_DIR, "PK_F1838_CASE2_PILOT_RECEIPT.json")
REMESH_RECEIPT_PATH = os.path.join(OUT_DIR, "PK_F1838_CASE2_PILOT_REMESH_RECEIPT.json")
ADAPTED_MESH_INP = os.path.join(OUT_DIR, "PK_F1838_CASE_2_PILOT_PHYS.inp")
DONOR_ODB_PATH = os.path.join(OUT_DIR, "PK_F1838_CASE2_FRAME300_DONOR.odb")

FIG_PNG = os.path.join(REPO_ROOT, "results", "figures", "fig_f1838_case2_pilot_mesh.png")
FIG_PDF = os.path.join(REPO_ROOT, "results", "figures", "fig_f1838_case2_pilot_mesh.pdf")

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA256 = "B0857C521AE8E212C74F711CC3373AD57B081167727104905A0F4D2FBBDA0129"
INTERFACE_SUBROUTINE_SHA256 = "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2"

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
    """Verify bitwise preservation of frozen production UEL and framework."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "171_c6_package171_r1_c3_0_reequilibration", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), "Frozen UEL must exist"
    assert sha256_file(uel_path) == FROZEN_UEL_SHA256, "Frozen UEL must remain bitwise identical"

    fw_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    assert os.path.exists(fw_path), "Frozen framework must exist"
    assert sha256_file(fw_path) == FROZEN_FRAMEWORK_SHA256, "Frozen framework must remain bitwise identical"

def test_interface_subroutine_integrity():
    """Verify F1830 candidate interface subroutine checksum."""
    int_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "271_f1830_stress_output_interface", "f42_native_miseseri_interface_v1.for")
    assert os.path.exists(int_path), "Interface subroutine must exist"
    assert sha256_file(int_path) == INTERFACE_SUBROUTINE_SHA256, "Interface subroutine must match F1830 candidate hash"

def test_pbs_accounting_and_scope():
    """Verify exactly 1 PBS job was submitted and recorded for Case 2 pilot only."""
    assert os.path.exists(RECEIPT_PATH), "Pilot receipt must exist"
    with open(RECEIPT_PATH, "r") as f:
        rec = json.load(f)
    assert rec["task_id"] == "F1838-CASE2-NATIVE-JOB1-PILOT"
    assert rec["pbs_job_id"] == "1424198.mmaster02"
    assert rec["solver_status"] == "COMPLETED_EXIT_0"

    task_json = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json, "r", encoding="utf-8-sig") as f:
        t = json.load(f)
    assert t["cumulative_pbs_submissions"] == 36

def test_mechanical_equivalence():
    """Verify peak reaction force and displacement match coarse baseline <= 0.01%."""
    with open(RECEIPT_PATH, "r") as f:
        rec = json.load(f)
    me = rec["mechanical_equivalence"]
    assert me["f_max_relative_diff_pct"] <= 0.01, "F_max relative difference must be <= 0.01%"
    assert me["u_at_f_max_relative_diff_pct"] <= 0.01, "u(F_max) relative difference must be <= 0.01%"
    assert me["equivalence_status"] == "PASS"

def test_native_miseseri_output_telemetry():
    """Verify native MISESERI and MISESAVG are present, non-zero, and cutbacks recovered."""
    with open(RECEIPT_PATH, "r") as f:
        rec = json.load(f)
    telemetry = rec["telemetry"]
    assert telemetry["native_miseseri_present"] is True
    assert telemetry["native_misesavg_present"] is True
    assert telemetry["total_elements_with_miseseri"] == 2906
    assert telemetry["step2_converged_increments"] >= 330
    assert telemetry["cutback_recovered_successfully"] is True

def test_single_frame_donor_odb_integrity():
    """Verify extracted single-frame donor ODB exists and contains expected frame."""
    assert os.path.exists(DONOR_ODB_PATH), "Donor ODB must exist"
    assert os.path.getsize(DONOR_ODB_PATH) == 7512588, "Donor ODB size must match exactly"
    assert sha256_file(DONOR_ODB_PATH) == "84622470D9B5DD86837030E4F7977308844B7D0B4DEF3AC444ACA609C4A4A78F"
    with open(REMESH_RECEIPT_PATH, "r") as f:
        rrec = json.load(f)
    assert rrec["donor_frame"]["step"] == "Step-2"
    assert rrec["donor_frame"]["frame_idx"] == 300
    assert rrec["donor_frame"]["d_max"] == 0.9972

def test_case2_pilot_finite_element_quality_gates():
    """Verify Gate 01, Gate 02, Gate 03, Gate 06, Gate 07 on adapted physical mesh."""
    assert os.path.exists(REMESH_RECEIPT_PATH), "Remesh receipt must exist"
    with open(REMESH_RECEIPT_PATH, "r") as f:
        rrec = json.load(f)

    audit = rrec["audit_metrics"]
    assert audit["total_elements"] == 28165
    assert audit["quad_count"] == 27481
    assert audit["tri_count"] == 684
    # Gate 02: Quad fraction >= 85%
    assert audit["quad_fraction_pct"] >= 85.0
    assert pytest.approx(audit["quad_fraction_pct"], 0.01) == 97.57
    # Gate 01: Positive Jacobians (min det(J) > 0, 0 nonpositive)
    assert audit["min_det_j"] > 0.0
    assert audit["non_positive_jacobians"] == 0
    # Gate 03: Aspect ratio (< 4.0, 0 violations)
    assert audit["max_aspect_ratio"] < 4.0
    assert audit["aspect_ratio_violations_gt_4"] == 0
    assert audit["median_aspect_ratio"] < 1.3
    # Gate 06: Coarsening ratio (1.7325x, FAIL against >= 2.0x)
    assert audit["gate_06_status"] == "FAIL"
    assert pytest.approx(audit["gate_06_coarsening_ratio"], 0.01) == 1.73
    # Gate 07: Budget (< 80,000, PASS)
    assert audit["gate_07_status"] == "PASS"
    assert audit["gate_07_element_count"] == 28165
    # Provenance classification: must be native
    assert audit["provenance_classification"] == "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR"

def test_spatial_resolution_and_distal_refinement():
    """Verify active refinement and recomputed zone metrics in the outer distal ligament."""
    with open(REMESH_RECEIPT_PATH, "r") as f:
        rrec = json.load(f)
    sp = rrec["spatial_metrics"]
    assert sp["outer_distal_count"] == 10280, "Outer distal ligament must have exactly 10,280 elements"
    assert sp["notch_to_hole_count"] == 807, "Notch-to-hole ligament must have exactly 807 elements"
    assert sp["outer_distal_cov_half_pct"] >= 94.0, "Distal ligament coverage at h <= l0/2 must be >= 94%"
    assert sp["fine_elements_le_l0_count"] == 24218

def test_visualization_figures_existence():
    """Verify PNG and PDF mesh figures exist with valid non-empty size."""
    assert os.path.exists(FIG_PNG), "Figure PNG must exist"
    assert os.path.exists(FIG_PDF), "Figure PDF must exist"
    assert os.path.getsize(FIG_PNG) == 4604809
    assert os.path.getsize(FIG_PDF) == 2367946
