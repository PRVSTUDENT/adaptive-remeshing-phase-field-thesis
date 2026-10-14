"""Unit test suite for Task F1408 Mode-I Method B Preliminary Evaluation and Final Adaptive Solve.

Verifies:
1. Preliminary runs (1S, 2S, 4S) prove exact step-partition invariance in METHOD_B_PRE_COMPARISON_SUMMARY.json.
2. Root cause of companion stress zeroing in f42_mixed_uel.for.
3. Final fracture deck (ET2 6,112 FE) geometry, boundary conditions, and hash integrity.
4. Final fracture PBS execution script governance (1 CPU serial anchor, 16 GB, entry_imfdfkmq, 24h).
5. Coordination ledgers consistency (HPC_JOB_LEDGER.csv, ACTIVE_TASK.json).
6. Frozen UEL hash integrity.
"""

import json
import os
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PRE_DIR = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_preliminary")
SUMMARY_JSON_PATH = os.path.join(PRE_DIR, "METHOD_B_PRE_COMPARISON_SUMMARY.json")
FINAL_PBS_PATH = os.path.join(PRE_DIR, "final_fracture", "submit_M1_MB_FINAL_1S.pbs")
FINAL_INP_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "34_stage14_step2_adaptive_candidate_et2_6k", "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp"
)
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
JOB_LEDGER_PATH = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
ACTIVE_TASK_PATH = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")


def test_f1408_preliminary_runs_completed_and_step_invariant():
    """Verify that preliminary runs 1S, 2S, 4S produced bitwise identical fields and step invariance."""
    assert os.path.isfile(SUMMARY_JSON_PATH), "Summary JSON missing: %s" % SUMMARY_JSON_PATH

    with open(SUMMARY_JSON_PATH, "r") as f:
        data = json.load(f)

    # Check cases
    cases = data.get("cases", {})
    assert len(cases) == 3, "Expected 3 preliminary cases (1S, 2S, 4S), found %d" % len(cases)
    for case_name in ["1S", "2S", "4S"]:
        assert case_name in cases, "Missing case %s" % case_name

    # Check comparison metrics
    comp = data.get("comparison", {})
    assert comp["common_miseseri_elements"] == 2906, "Expected 2906 common elements"
    assert comp["delta_rf_2s_vs_1s"] == 0.0, "Delta RF 2S vs 1S is non-zero"
    assert comp["delta_rf_4s_vs_1s"] == 0.0, "Delta RF 4S vs 1S is non-zero"
    assert comp["max_diff_miseseri_2s_1s"] == 0.0, "MISESERI 2S vs 1S diff is non-zero"
    assert comp["max_diff_miseseri_4s_1s"] == 0.0, "MISESERI 4S vs 1S diff is non-zero"

    # Terminal displacements and forces
    u2_dict = comp["terminal_u2"]
    rf2_dict = comp["terminal_rf2"]
    for case_name in ["1S", "2S", "4S"]:
        assert abs(u2_dict[case_name] - 0.0050) < 1e-6, "Terminal displacement mismatch for %s" % case_name
        assert abs(rf2_dict[case_name] - 0.65308857) < 1e-4, "Terminal RF mismatch for %s" % case_name


def test_f1408_companion_stress_zeroing_root_cause():
    """Verify that f42_mixed_uel.for explicitly sets STRESS=0.D0 in companion UMAT layer."""
    assert os.path.isfile(UEL_PATH), "UEL missing: %s" % UEL_PATH

    with open(UEL_PATH, "r") as f:
        content = f.read()

    # Verify companion stress zeroing exists
    assert "STRESS(I) = 0.D0" in content or "STRESS(i) = 0.0D0" in content or "STRESS(I)=0.D0" in content, \
        "Companion UMAT STRESS zeroing card not found in UEL"


def test_f1408_final_fracture_deck_and_mesh_specifications():
    """Verify that final fracture deck has valid hash, 6,112 FE, roller BCs, and correct displacement target."""
    assert os.path.isfile(FINAL_INP_PATH), "Final deck missing: %s" % FINAL_INP_PATH

    # SHA256 verification
    h = hashlib.sha256()
    with open(FINAL_INP_PATH, "rb") as f:
        h.update(f.read())
    deck_sha = h.hexdigest().upper()
    assert deck_sha == "B5135AF51026FE2ABC4D3A0471567E7F6D55299A53A2D3501BCE61C3146FE36D", "Final deck hash altered"

    with open(FINAL_INP_PATH, "r") as f:
        lines = f.readlines()

    # Count nodes and elements
    in_nodes = False
    in_elems = False
    node_count = 0
    elem_count = 0
    has_roller_bc = False

    for line in lines:
        line_clean = line.strip().upper()
        if line_clean.startswith("*NODE"):
            in_nodes = True
            in_elems = False
            continue
        elif line_clean.startswith("*ELEMENT"):
            in_nodes = False
            in_elems = True
            continue
        elif line_clean.startswith("*"):
            in_nodes = False
            in_elems = False

        if in_nodes and line_clean:
            node_count += 1
        elif in_elems and line_clean:
            elem_count += 1

        if "N_BOTTOM, 2, 2" in line_clean:
            has_roller_bc = True

    assert node_count == 6186, "Expected 6186 total nodes (6181 mesh + 5 RP/aux), found %d" % node_count
    # 3 layers of 6112 elements = 18336 element lines + 2 auxiliary elements = 18338
    assert elem_count == 18338, "Expected 18338 element cards (18336 layered + 2 aux), found %d" % elem_count
    assert has_roller_bc, "Missing roller boundary condition N_BOTTOM, 2, 2"


def test_f1408_final_fracture_pbs_governance():
    """Verify that final fracture PBS script adheres to all execution governance rules."""
    assert os.path.isfile(FINAL_PBS_PATH), "PBS script missing: %s" % FINAL_PBS_PATH

    with open(FINAL_PBS_PATH, "r") as f:
        pbs_content = f.read()

    assert "#PBS -q entry_imfdfkmq" in pbs_content, "PBS queue must be entry_imfdfkmq"
    assert "#PBS -l nodes=1:ppn=1" in pbs_content, "Must request 1 CPU serial anchor"
    assert "#PBS -l walltime=24:00:00" in pbs_content, "Must request 24h walltime"
    assert "#PBS -l mem=16gb" in pbs_content, "Must request 16gb RAM"
    assert "#PBS -m abe" in pbs_content, "Dual-channel PBS mail missing"
    assert "job_notifications.sh" in pbs_content, "Notification wrapper missing"
    assert "notification_install_terminal_trap" in pbs_content, "Terminal notification trap missing"
    assert "cpus=1" in pbs_content, "Solver execution must specify cpus=1"


def test_f1408_coordination_ledgers_consistency():
    """Verify that HPC_JOB_LEDGER and ACTIVE_TASK record preliminary completion and final active solve."""
    assert os.path.isfile(JOB_LEDGER_PATH), "Job ledger missing: %s" % JOB_LEDGER_PATH
    assert os.path.isfile(ACTIVE_TASK_PATH), "Active task missing: %s" % ACTIVE_TASK_PATH

    with open(JOB_LEDGER_PATH, "r") as f:
        ledger_text = f.read()

    assert "1411891.mmaster02" in ledger_text, "Job 1411891 missing from ledger"
    assert "1411892.mmaster02" in ledger_text, "Job 1411892 missing from ledger"
    assert "1411893.mmaster02" in ledger_text, "Job 1411893 missing from ledger"
    assert "1411895.mmaster02" in ledger_text, "Job 1411895 missing from ledger"

    with open(ACTIVE_TASK_PATH, "r") as f:
        task_data = json.load(f)

    assert task_data.get("task_id").startswith("F14")
    assert "1411895.mmaster02" in task_data.get("active_pbs_job_ids", []) or "1411895.mmaster02" in task_data.get("completed_pbs_job_ids", [])


def test_f1408_frozen_baseline_uel_hash_integrity():
    """Verify that the frozen baseline UEL has not been modified."""
    assert os.path.isfile(UEL_PATH), "Frozen UEL missing: %s" % UEL_PATH

    h = hashlib.sha256()
    with open(UEL_PATH, "rb") as f:
        h.update(f.read())
    uel_sha = h.hexdigest().upper()
    assert uel_sha == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", "Frozen UEL hash altered!"
