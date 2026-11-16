# -*- coding: utf-8 -*-
"""
tests/unit/test_f1804_case2_distal_recovery.py
================================================
Task F1804 Unit Test: Case 2 Distal Degraded-Modulus Recovery Donor and Native Remesh.

Validates:
1. Authentic donor qualification receipt and elementwise degraded modulus constitutive treatment.
2. Stress transfer and recovery error concentration in outer distal corridor (41.47 MPa vs 5.84 MPa far field).
3. Physical adapted mesh generation, quad fraction >= 90%, min det(J) > 0, max aspect ratio <= 4.0.
4. Distal corridor resolution enhancement: % <= l0/2 reaches 72.10% (+5.76 pts vs F1795 baseline 66.34%).
5. Far-field coarsening (3.63x >= 2.0x) and computational efficiency (13,061 vs 35,648 elements, -63.36%).
6. Preservation of canonical quality gates (Gates 01-07 all PASS).
7. Governance invariants: frozen production UEL, zero new PBS submissions, cumulative 35, MASTER_GOAL_STATUS = OPEN.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
PERMANENT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "254_f1804_case2_distal_recovery")
DONOR_RECEIPT = os.path.join(PERMANENT_DIR, "PK_F1804_CASE2_DONOR_RECEIPT.json")
REMESH_RECEIPT = os.path.join(PERMANENT_DIR, "PK_F1804_CASE2_REMESH_RECEIPT.json")
PHYS_INP = os.path.join(PERMANENT_DIR, "PK_F1804_CASE_2_ADAPT_PHYS.inp")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1804_case2_native_miseseri.json")
DAMAGE_RECORD = os.path.join(REPO_ROOT, "results", "validation", "f1804_case2_postbreach_damage_record.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1804_CASE2_DISTAL_DEGRADED_MODULUS_RECOVERY_REPORT.md")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
FW_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FW_SHA256 = "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D"
EXPECTED_DONOR_SHA256 = "35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1804_donor_qualification_and_constitutive_fidelity():
    """Verify donor qualification receipt declares elementwise degraded-modulus fidelity."""
    assert os.path.exists(DONOR_RECEIPT), "Donor qualification receipt missing"
    with open(DONOR_RECEIPT, "r") as f:
        donor = json.load(f)

    assert donor["odb_sha256"] == EXPECTED_DONOR_SHA256
    assert donor["odb_size_bytes"] == 7417896
    assert donor["causal_source"]["step_name"] == "Step-2"
    assert donor["causal_source"]["frame_index"] == 190
    assert donor["causal_source"]["physical_state"] == "POST_BREACH_HOLE_ARREST"
    assert abs(donor["causal_source"]["frame_time_s"] - 0.3737) < 0.001
    assert abs(donor["causal_source"]["uy_top_mm"] - 0.007616) < 0.0001

    rec = donor["recovery_model"]
    assert rec["constitutive_treatment"] == "ELEMENTWISE_EXACT_DEGRADED_ELASTIC"
    assert rec["E0_mpa"] == 210000.0
    assert rec["nu"] == 0.30
    assert rec["k_res"] == 1.0e-7
    assert rec["num_elements"] == 2906
    assert rec["min_degraded_E_mpa"] < 10.0, "Min degraded E should be ~5.32 MPa"
    assert rec["elements_with_d_ge_080"] == 11

    reg = donor["regional_error_distribution_mpa"]
    assert reg["global_mean_miseseri"] > 10.0
    assert reg["outer_distal_corridor_mean_miseseri"] > 40.0
    assert reg["far_field_mean_miseseri"] < 10.0
    assert reg["outer_distal_corridor_mean_miseseri"] / reg["far_field_mean_miseseri"] > 5.0

    gates = donor["quality_gates"]
    assert gates["GATE_01_SOLVER_COMPLETION_EXIT_0"] == "PASS"
    assert gates["GATE_02_ALL_ELEM_SET_PRESENT"] == "PASS"
    assert gates["GATE_03_MISESERI_NONZERO_ACTIVE"] == "PASS"
    assert gates["GATE_04_CAUSAL_HORIZON_ENFORCED"] == "PASS"


def test_f1804_physical_mesh_quality_and_invariants():
    """Verify physical adapted mesh generation, quad fraction, Jacobians, and aspect ratios."""
    assert os.path.exists(PHYS_INP), "Physical mesh file missing: " + PHYS_INP
    assert os.path.getsize(PHYS_INP) == 942941
    actual_mesh_sha = sha256_file(PHYS_INP)
    assert actual_mesh_sha == "FDDA676278B096D66C1392528921BE8E3DC54CB3C1B822BD038AA17F855E43E8"

    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    fe = data["finite_element_quality"]
    assert fe["total_elements"] == 13061
    assert fe["quad_count"] == 12699
    assert fe["tri_count"] == 362
    assert fe["quad_percent"] >= 90.0, "Quad percent must be >= 90%"
    assert fe["quad_percent"] > 97.0
    assert fe["min_det_j"] > 0.0, "Signed Jacobian must be strictly positive"
    assert fe["nonpositive_jacobians"] == 0, "Zero non-positive Jacobians required"
    assert fe["max_aspect_ratio"] <= 4.0, "Max aspect ratio must be <= 4.0"
    assert fe["max_aspect_ratio"] < 2.5
    assert fe["aspect_ratio_violations_gt_4"] == 0
    assert fe["min_corner_angle_deg"] > 30.0
    assert fe["max_corner_angle_deg"] < 140.0


def test_f1804_distal_corridor_resolution_enhancement():
    """Verify distal corridor % <= l0/2 surpasses F1795 baseline (66.34% -> 72.10%)."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    sp = data["spatial_resolution_profile"]
    dist = sp["outer_distal_corridor"]

    assert dist["count"] > 3000
    assert dist["pct_le_l0"] > 95.0, "Distal % <= l0 must be > 95%"
    assert dist["pct_le_l0_half"] > 70.0, "Distal % <= l0/2 must exceed 70%"
    assert abs(dist["pct_le_l0_half"] - 72.10) < 0.5
    assert dist["min_h_mm"] < 0.0010, "Min distal h should be ~0.81 um"

    comp = data["comparative_resolution_vs_f1795_preanalysis"]
    assert comp["distal_pct_le_l0_half_delta_pts"] > 5.0, "Must improve by > +5.0 percentage points"


def test_f1804_mesh_efficiency_and_far_field_coarsening():
    """Verify computational efficiency (13,061 vs 35,648 elements) and far-field coarsening."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    fe = data["finite_element_quality"]
    assert fe["total_elements"] == 13061
    assert fe["total_elements"] < 20000, "Must be well below 20,000 elements"

    sp = data["spatial_resolution_profile"]
    coarsening = sp["far_to_distal_coarsening_ratio"]
    assert coarsening >= 2.0, "Far-to-distal coarsening ratio must be >= 2.0x"
    assert coarsening > 3.5


def test_f1804_canonical_quality_gates():
    """Verify all 7 canonical quality gates pass."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    gates = data["quality_gates"]
    assert gates["GATE_01_NATIVE_EXECUTION_EXIT_0"] == "PASS"
    assert gates["GATE_02_QUAD_FRACTION_GE_90_PCT"] == "PASS"
    assert gates["GATE_03_ZERO_NEGATIVE_JACOBIANS"] == "PASS"
    assert gates["GATE_04_ASPECT_RATIO_LE_4"] == "PASS"
    assert gates["GATE_05_DISTAL_CORRIDOR_RESOLUTION"] == "PASS"
    assert gates["GATE_06_FAR_FIELD_COARSENING"] == "PASS"
    assert gates["GATE_07_COMPUTATIONAL_EFFICIENCY"] == "PASS"


def test_f1804_governance_and_coordination_invariants():
    """Verify active task, session lock, UEL hash, and zero new PBS submissions."""
    task_file = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_file, "r") as f:
        task = json.load(f)

    assert task["task_id"] == "F1804-CASE2-DISTAL-DEGRADED-MODULUS-RECOVERY-REMESH"
    assert task["master_goal_status"] == "OPEN"
    assert task["frozen_uel_sha256"] == FROZEN_UEL_SHA256
    assert task["cumulative_pbs_submissions"] == 35
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0

    assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA256
    assert sha256_file(FW_PATH) == FROZEN_FW_SHA256


if __name__ == "__main__":
    pytest.main(["-v", __file__])
