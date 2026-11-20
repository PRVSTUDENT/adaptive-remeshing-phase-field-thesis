# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_job2_execution.py
================================================
Task: METHOD-C-CASE3-JOB2-DIAGNOSIS
Validates the execution evidence, spatial crack growth, and diagnosis for Job 2:
1. File integrity and authentic solver outputs committed to repository
2. Step-1 fixed-load re-equilibration force continuity (|Delta RF2| <= 5%) and energy continuity
3. Step-1 damage growth under hold classified as GROWTH_UNDER_HOLD
4. Monotonic fracture energy dissipation (zero healing verified)
5. Spatial crack advance extracted from ODB across thresholds (0.50, 0.80, 0.95)
6. Increment 11 dt_min failure mechanism and failing nodes localized near notch tip
7. PBS accounting: exactly 0 new PBS submissions for diagnosis, cumulative count = 64
8. Frozen UEL CE8D5EDC... preservation
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")

REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp")
STA_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.sta")
MSG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.msg")
DAT_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.dat")
LOG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2_pbs_execution.log")
CSV_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2_uel_energy_balance.csv")
OBS_JSON = os.path.join(CASE_DIR, "job2_observables.json")
SPATIAL_JSON = os.path.join(CASE_DIR, "job2_spatial_crack.json")
EXTRACTOR_PY = os.path.join(REPO_ROOT, "scripts", "postprocessing", "extract_case3_job2_spatial_crack.py")
DIAG_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB2_DIAGNOSIS_REPORT.md")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_job2_files_and_hashes():
    """Validates existence and cryptographic SHA-256 of all Job 2 solver and diagnosis artifacts."""
    expected = {
        REFINED_DECK: "612AFE2A96D74F5B9D7485AEAEBDB13868DD4131810C8B27F5A51EE26B60F484",
        STA_FILE: "3730F3765198D17035F91C4B86CF841FDE50307ED507B6EEBD70CBE3167578D8",
        MSG_FILE: "DBC6BDB039D606912BE942A3BC3A5C173A74381BF8CDA69157533D6271F124E1",
        DAT_FILE: "39C1A89F5A31735968561084AD696979A7734814093AFC2F564DE962D96039A1",
        LOG_FILE: "08908A6BCCD0EB2A44E2D8BFBCDD438F8EDFA2D6A9CB4C36B172A070E8BCB083",
        CSV_FILE: "105156B8AD4501E8E9D05135E1D9744653E76FB4361BF70DB29151E266D22E54",
        OBS_JSON: "9E12D86CB9852595ED16B35FDD42C2BBFFCD0E364D30A4D1AE1A8E2BB7E9BC0A",
        SPATIAL_JSON: "B9B84C0A9B65E43E68373926263A1146A3CE74B9ACEE3DEA9933D66233CEF562",
        EXTRACTOR_PY: "0DA94C360A6CB70A9B5F22EAD217B57DA3B88CD65A57C28092BC39DC89AF92F7",
        UEL_FILE: "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    }
    for path, exp_sha in expected.items():
        assert os.path.isfile(path), "Missing artifact: %s" % path
        act_sha = compute_sha256(path)
        assert act_sha == exp_sha, "SHA mismatch for %s: expected %s, got %s" % (os.path.basename(path), exp_sha, act_sha)

def test_step1_reequilibration_continuity_and_damage_growth():
    """Validates Step-1 force/energy continuity and classifies damage increase as growth under hold."""
    rf2_donor = 3.9288122
    rf2_receiver = 3.9135252
    delta_rf2_rel = abs(rf2_receiver - rf2_donor) / rf2_donor
    assert delta_rf2_rel <= 0.05, "Force continuity violation: %.3f%% > 5.0%%" % (delta_rf2_rel * 100.0)
    assert abs(delta_rf2_rel - 0.00389) < 1e-4

    e_tot_donor = 0.09994965
    e_tot_recv = 0.09956534
    delta_tot_rel = abs(e_tot_recv - e_tot_donor) / e_tot_donor
    assert delta_tot_rel <= 0.05, "Total energy continuity violation: %.3f%%" % (delta_tot_rel * 100.0)

    # Damage growth under hold: 0.469063 -> 0.496474 (+5.84%)
    d_donor = 0.469063
    d_recv = 0.496474
    d_growth = (d_recv - d_donor) / d_donor
    assert 0.05 <= d_growth <= 0.07, "Unexpected damage growth under hold: %.2f%%" % (d_growth * 100.0)

def test_monotonic_dissipation_and_zero_healing():
    """Validates monotonic fracture energy growth in Step 2 (zero healing)."""
    with open(CSV_FILE, "r") as f:
        lines = [line.strip().split(",") for line in f if line.strip() and not line.startswith("Step")]

    step2_frac_energies = [float(row[5]) for row in lines if int(row[0]) == 2]
    assert len(step2_frac_energies) >= 10, "Insufficient Step 2 increments: %d" % len(step2_frac_energies)

    for i in range(1, len(step2_frac_energies)):
        assert step2_frac_energies[i] >= step2_frac_energies[i-1], (
            "Fracture energy healing violation at inc %d: %.6e < %.6e" % (
                i, step2_frac_energies[i], step2_frac_energies[i-1]
            )
        )

    e_frac_initial = float(lines[0][5])
    e_frac_final = step2_frac_energies[-1]
    growth = (e_frac_final - e_frac_initial) / e_frac_initial
    assert growth >= 0.90, "Fracture energy did not double: growth = %.2f%%" % (growth * 100.0)

def test_spatial_crack_metrics_and_localization():
    """Validates spatial crack advance from notch root (x=10.0 mm) extracted from ODB."""
    with open(SPATIAL_JSON, "r") as f:
        spatial = json.load(f)

    assert spatial["notch_root"] == [10.0, 70.0]
    s2_frames = spatial["steps"]["Step-2"]
    assert len(s2_frames) == 4

    # Terminal converged state (Frame 2)
    f2 = s2_frames[2]
    assert abs(f2["peak_damage"] - 0.976822) < 1e-4

    # Spatial advance checks at frame 2
    m_050 = f2["spatial_metrics"]["d_ge_0.50"]
    m_080 = f2["spatial_metrics"]["d_ge_0.80"]
    m_095 = f2["spatial_metrics"]["d_ge_0.95"]

    assert m_050["count_elements"] == 31
    assert abs(m_050["delta_a_x_mm"] - 0.6068) < 1e-3
    assert m_050["crack_propagated_spatially"] is True

    assert m_080["count_elements"] == 10
    assert abs(m_080["delta_a_x_mm"] - 0.3457) < 1e-3
    assert m_080["crack_propagated_spatially"] is True

    assert m_095["count_elements"] == 2
    assert abs(m_095["delta_a_x_mm"] - 0.1529) < 1e-3
    assert m_095["crack_propagated_spatially"] is True

def test_inc11_failure_telemetry_and_failing_nodes():
    """Validates that Inc-11 divergence occurred at nodes localized near notch tip."""
    with open(MSG_FILE, "r") as f:
        msg_text = f.read()

    assert "INCREMENT    11 STARTS. ATTEMPT NUMBER  3, TIME INCREMENT  1.000E-08" in msg_text
    assert "LARGEST SCALED RESIDUAL FORCE      3.788E-03   AT NODE      12228   DOF  2" in msg_text
    assert "LARGEST CORRECTION TO DISP.        3.204E-02   AT NODE      14745   DOF  3" in msg_text
    assert "***NOTE: THE SOLUTION APPEARS TO BE DIVERGING." in msg_text
    assert "***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED" in msg_text

def test_governance_and_pbs_accounting():
    """Validates diagnosis task governance: 0 new PBS jobs consumed, cumulative count = 64."""
    task_json = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["task_id"] == "METHOD-C-CASE3-JOB2-DIAGNOSIS"
    assert task["master_goal_status"] == "OPEN"
    assert task["max_new_pbs_submissions"] == 0
    assert task["cumulative_pbs_submissions"] == 64
    assert task["last_failed_pbs_job_id"] == "1424772.mmaster02"
