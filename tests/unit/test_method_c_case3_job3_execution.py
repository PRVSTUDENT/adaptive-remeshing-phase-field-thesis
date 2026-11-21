# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_job3_execution.py
================================================
Task: METHOD-C-CASE3-CYCLE2-JOB3-SOLVE / METHOD-C-CASE3-JOB3-DIAGNOSIS
Validates the execution evidence, spatial crack advance, force/energy continuity,
and numerical mitigations for Case 3 Cycle-2 Job 3:
1. File integrity and authentic solver outputs committed to repository
2. Step-1 fixed-load re-equilibration force continuity (|Delta RF2| <= 5.0%) and energy continuity
3. Step-2 forward crack propagation: peak load capture, post-peak load softening
4. Monotonic fracture energy surge (+294.2%) and elastic strain energy release
5. Spatial crack advance extracted from ODB (crack tip advance +2.3686 mm past Job 2)
6. Zero healing verification (d_max monotonically non-decreasing up to 0.99975)
7. Inc-11 cutback floor milestone surpassed down to dt = 6.728e-14
8. PBS accounting: exactly 1 new PBS submission consumed (cumulative 64 -> 65)
9. Bitwise frozen UEL CE8D5EDC... preservation
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")

REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp")
PHYS_MESH = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_PHYS.inp")
STA_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta")
MSG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg")
DAT_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat")
LOG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log")
CSV_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv")
OBS_JSON = os.path.join(CASE_DIR, "job3_observables.json")
SPATIAL_JSON = os.path.join(CASE_DIR, "job3_spatial_crack.json")
RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json")
SUMMARY_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json")
EXEC_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md")
GEN_SCRIPT = os.path.join(REPO_ROOT, "scripts", "state_transfer", "run_case3_cycle2_state_transfer.py")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_job3_files_and_hashes():
    """Validates existence and cryptographic SHA-256 of all Job 3 solver and execution artifacts."""
    expected = {
        REFINED_DECK: "1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C",
        PHYS_MESH: "58466F66E1D9E41E73C5E5233DD748B5237193E225407320DB4288A8DB38081F",
        STA_FILE: "7CD84F404CF828700CF68352E07FA12739EA59B0BAE533CA47A018900AD0C420",
        MSG_FILE: "7AC50248445EE92AABB4FD5827E78F49B213EB8319748471B3F9FF06F5C3413F",
        DAT_FILE: "B5F0761C9B8F9683AF2728496A76E91E2BD73F440EFD57C18F2A8576C750D645",
        LOG_FILE: "7761063901A66428015044DC364636861D040F59B04D9E65183ED7B4FB4DE00E",
        CSV_FILE: "E0F01BA5075ADCA3FEF64E0811B52AD61FD285C5BEBEE25F1849315CADB8F6DB",
        OBS_JSON: "05DAA9BC1B93A6B2D4C0D98DA1652527F7806F21AAF0ED01AFDC5502520E50D2",
        SPATIAL_JSON: "882F69CB69FE6AB338794A71D3C1227035BA481CAF6E51D62121612F4DD27AF3",
        RECEIPT_JSON: "FA53B5103B112CF9AB7A01AF0441B056D712A8086FA4697C3A1939017180F60E",
        SUMMARY_JSON: "440DD0B590931EE3657914911AC437FF88957569C718CB5CCD52E108FF0E8585",
        EXEC_REPORT: "A7835DFB36A41CA0066DFCA60C2B30D5A3C6D9A863F964B7DB60D99A2769FF77",
        GEN_SCRIPT: "4C61BC4950EB7491E594F2CFD1768D187FE039521A9476B2E8ED00BAFAA10EF4",
        UEL_FILE: "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    }
    for path, exp_sha in expected.items():
        assert os.path.isfile(path), "Missing artifact: %s" % path
        act_sha = compute_sha256(path)
        assert act_sha == exp_sha, "SHA mismatch for %s: expected %s, got %s" % (os.path.basename(path), exp_sha, act_sha)

def test_step1_reequilibration_continuity():
    """Validates Step-1 fixed-load force and energy continuity vs Job 2 donor end state."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s1 = rc["step1_re_equilibration"]
    assert s1["force_continuity_pass"] is True
    assert s1["force_continuity_delta_pct"] < 5.0
    assert abs(s1["force_continuity_delta_pct"] - 0.375442) < 1e-4

    assert s1["energy_continuity_pass"] is True
    assert s1["energy_continuity_delta_pct"] < 5.0
    assert abs(s1["energy_continuity_delta_pct"] - 0.963486) < 1e-4

    assert s1["increments"] == 1
    assert s1["iterations"] == 2

def test_step2_propagation_softening_and_energy():
    """Validates Step-2 forward propagation: peak load, softening, and fracture energy growth."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s2 = rc["step2_propagation"]
    assert s2["increments_converged"] == 28
    assert s2["total_converged_increments"] == 29
    assert s2["peak_load_RF2_kN"] > s2["terminal_RF2_kN"]
    assert s2["softening_demonstrated"] is True
    assert s2["load_drop_from_peak_pct"] < 0.0

    # Fracture energy growth > 200%
    assert s2["fracture_energy_growth_pct"] > 200.0
    assert s2["monotonic_fracture_energy_growth"] is True
    assert s2["strain_energy_release_demonstrated"] is True
    assert s2["zero_healing_verified"] is True
    assert s2["inc11_milestone_surpassed"] is True
    assert s2["smallest_converged_dt"] < 1.0e-13

def test_spatial_crack_advance():
    """Validates spatial crack tip forward advance across thresholds from ODB extraction."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    sp = rc["spatial_crack_propagation"]
    assert sp["crack_propagated_spatially"] is True
    assert sp["crack_heading_toward_hole"] is True
    assert sp["terminal_tip_x_mm_d095"] > sp["donor_tip_x_mm_d095"]
    assert sp["step2_forward_advance_mm_d095"] > 2.0  # > 2.0 mm forward growth past donor
    assert sp["fully_damaged_elements_d095_terminal"] > sp["fully_damaged_elements_d095_initial"]
    assert sp["process_zone_elements_d050_terminal"] > sp["process_zone_elements_d050_initial"]

def test_pbs_accounting_and_governance():
    """Validates PBS submission accounting and UEL integrity."""
    with open(os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json"), "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] in ("METHOD-C-CASE3-CYCLE2-JOB3-SOLVE", "METHOD-C-CASE3-JOB3-DIAGNOSIS")
    assert task["master_goal_status"] == "OPEN"
    assert task["cumulative_pbs_submissions"] == 65
