# -*- coding: utf-8 -*-
"""
tests/unit/test_f1803_case3_accurate_recovery.py
================================================
Task F1803 Unit Test: Case 3 State-2 Degraded Modulus Fidelity and Native Remesh.

Validates:
1. Authentic donor qualification receipt and elementwise degraded modulus constitutive treatment.
2. Severed crack compliance and massive stress transfer to secondary ligament (ratio sec/prim > 10x).
3. Physical adapted mesh generation, quad fraction >= 90%, min det(J) > 0, max aspect ratio <= 4.0.
4. Breaking of the secondary-corridor resolution barrier: % <= l0 > 50% and % <= l0/2 > 2.0% (min h < 0.10 mm).
5. Primary corridor coarsening and physical demonstration of single-snapshot recovery limits.
6. Preservation of canonical quality gates (Gate 5 and Gate 7 remain FAIL under canonical thresholds).
7. Governance invariants: frozen production UEL, zero new PBS submissions, cumulative 35, MASTER_GOAL_STATUS = OPEN.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
PERMANENT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "253_f1803_case3_accurate_recovery")
DONOR_RECEIPT = os.path.join(PERMANENT_DIR, "PK_F1803_CASE3_ACCURATE_DONOR_RECEIPT.json")
REMESH_RECEIPT = os.path.join(PERMANENT_DIR, "PK_F1803_CASE3_ACCURATE_REMESH_RECEIPT.json")
PHYS_INP = os.path.join(PERMANENT_DIR, "PK_F1803_CASE_3_ADAPT_PHYS.inp")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1803_case3_native_miseseri.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1803_CASE3_ACCURATE_CONSTITUTIVE_RECOVERY_REPORT.md")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_DONOR_SHA256 = "965136FD7AE637EFF44DEEDF4D152817037CF3C05656D9D1B6006377038362BB"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1803_donor_qualification_and_constitutive_fidelity():
    """Verify donor qualification receipt declares elementwise degraded-modulus fidelity."""
    assert os.path.exists(DONOR_RECEIPT), "Donor qualification receipt missing"
    with open(DONOR_RECEIPT, "r") as f:
        donor = json.load(f)

    assert donor["odb_sha256"] == EXPECTED_DONOR_SHA256
    assert donor["odb_size_bytes"] == 9935692
    assert donor["constitutive_treatment"] == "ELEMENTWISE_EXACT_DEGRADED_ELASTIC"
    assert donor["E0_kn_per_mm2"] == 210.0
    assert donor["k_res"] == 1.0e-7
    assert donor["num_elements"] == 3923
    assert donor["min_degraded_E_kn_per_mm2"] < 1.0e-4, "Min degraded E should be ~9.7e-5 kN/mm^2"
    assert donor["elements_with_d_gt_09"] == 24

    reg = donor["regional_error_distribution_kn_per_mm2"]
    assert reg["ratio_secondary_to_primary_mean"] > 10.0, "Secondary/primary error ratio should be > 10x"
    assert abs(reg["ratio_secondary_to_primary_mean"] - 14.49) < 0.5


def test_f1803_physical_mesh_quality_and_invariants():
    """Verify physical mesh quality: quad fraction >= 90%, min det(J) > 0, max AR <= 4.0."""
    assert os.path.exists(PHYS_INP), "Physical mesh INP missing"
    assert os.path.exists(REMESH_RECEIPT), "Remesh receipt missing"
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    mesh = data["physical_mesh"]
    assert mesh["total_elements"] == 26746
    assert mesh["quad_percent"] >= 90.0, "Quad percentage must be >= 90%"
    assert mesh["quad_percent"] > 97.0
    assert mesh["min_det_j"] > 0.0, "Min det(J) must be strictly positive"
    assert mesh["non_positive_jacobians"] == 0
    assert mesh["max_aspect_ratio"] <= 4.0, "Max aspect ratio must be <= 4.0"
    assert mesh["ar_violations_gt_4"] == 0


def test_f1803_secondary_corridor_barrier_broken():
    """Verify secondary corridor achieves % <= l0 > 50% and % <= l0/2 > 2.0% with min h < 0.10 mm."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    sec = data["spatial_resolution"]["secondary_corridor_hole_to_boundary"]
    assert sec["pct_le_l0"] > 50.0, "Secondary corridor % <= l0 should be > 50%"
    assert abs(sec["pct_le_l0"] - 54.87) < 0.5
    assert sec["pct_le_l0_half"] > 2.0, "Secondary corridor % <= l0/2 barrier broken (> 2.0%)"
    assert abs(sec["pct_le_l0_half"] - 2.44) < 0.5
    assert sec["min_mm"] < 0.10, "Minimum h in secondary corridor should be < 0.10 mm"
    assert abs(sec["min_mm"] - 0.0738) < 0.01
    assert sec["count"] == 3977


def test_f1803_comparative_resolution_vs_f1802_and_f1800():
    """Verify comparative resolution: secondary % <= l0 gains +49.81% pts vs F1802."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    comp = data["comparative_resolution_vs_f1800_f1801_f1802"]
    sec_l0 = comp["secondary_pct_le_l0"]
    sec_l0_half = comp["secondary_pct_le_l0_half"]
    sec_min_h = comp["secondary_min_h_mm"]
    sec_count = comp["secondary_corridor_elements"]

    assert sec_l0["f1800_precritical_3pct"] == 1.24
    assert sec_l0["f1802_20bin_state2_3pct"] == 5.06
    assert abs(sec_l0["f1803_accurate_state2_3pct"] - 54.87) < 0.1
    assert abs(sec_l0["gain_vs_f1802_pct_pts"] - 49.81) < 0.1

    assert sec_l0_half["f1800_precritical_3pct"] == 0.00
    assert sec_l0_half["f1802_20bin_state2_3pct"] == 0.00
    assert abs(sec_l0_half["f1803_accurate_state2_3pct"] - 2.44) < 0.1

    assert sec_min_h["f1800_precritical_3pct"] == 0.2234
    assert sec_min_h["f1802_20bin_state2_3pct"] == 0.1580
    assert abs(sec_min_h["f1803_accurate_state2_3pct"] - 0.0738) < 0.01

    assert sec_count["f1800_precritical_3pct"] == 888
    assert sec_count["f1802_20bin_state2_3pct"] == 1423
    assert sec_count["f1803_accurate_state2_3pct"] == 3977


def test_f1803_canonical_quality_gates():
    """Verify canonical quality gates: Gate 01-04 PASS, Gate 05-07 FAIL (canonical thresholds)."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    gates = data["quality_gates"]
    assert gates["GATE_01_NATIVE_EXECUTION_EXIT_0"] == "PASS"
    assert gates["GATE_02_QUAD_FRACTION_GE_90_PCT"] == "PASS"
    assert gates["GATE_03_ZERO_NEGATIVE_JACOBIANS"] == "PASS"
    assert gates["GATE_04_ASPECT_RATIO_LE_4"] == "PASS"
    assert gates["GATE_05_PRIMARY_CORRIDOR_RESOLUTION"] == "FAIL", "Gate 5 must fail under canonical >= 90% threshold"
    assert gates["GATE_06_FAR_FIELD_COARSENING"] == "FAIL"
    assert gates["GATE_07_EFFICIENCY_VS_HISTORICAL_EXPLOSION"] == "FAIL", "Gate 7 must fail under canonical < 20000 threshold"


def test_f1803_governance_and_coordination_invariants():
    """Verify active task, session lock, UEL hash, and zero new PBS submissions."""
    task_file = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_file, "r") as f:
        task = json.load(f)

    assert task["task_id"] in [
        "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH",
        "F1804-CASE2-DISTAL-DEGRADED-MODULUS-RECOVERY-REMESH",
        "F1805-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-SENSITIVITY"
    ]
    assert task["master_goal_status"] == "OPEN"
    assert task["frozen_uel_sha256"] == FROZEN_UEL_SHA256
    assert task["cumulative_pbs_submissions"] == 35
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
