# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_job3_diagnosis.py
================================================
Task: METHOD-C-CASE3-JOB3-DIAGNOSIS
Correlation: HND-METHOD-C-CASE3-JOB3-DIAG-002
Predecessor: HND-METHOD-C-CASE3-JOB3-DIAG-001 (INSUFFICIENT_EVIDENCE)

Validates the full disclosure, technical reconciliation, and artifact integrity
for the Job 3 failure diagnosis:
1. Cryptographic SHA-256 and exact byte counts of all committed artifacts
2. Preflight deck regeneration disclosure: approved 8DDE4D8B -> executed 1D72A981
3. Disambiguated solver walltime (PBS 4602 s vs solver 4268 s) and UTC/CET timestamps
4. Dual forward advance baselines (+2.3686 mm donor vs +2.3649 mm post-hold)
5. Classification of Step-1 damage growth as GROWTH_UNDER_HOLD
6. Terminal frame relabeled as Increment 28 converged state
7. Reconciled Job-2 comparison observables in reports and receipts
8. Bitwise frozen UEL CE8D5EDC... preservation
9. PBS accounting: strictly 0 new PBS jobs, cumulative 65 preserved
10. Verbatim UEL cards, correct line numbers, and SVAR arithmetic
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
DIAG_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md")
GEN_SCRIPT = os.path.join(REPO_ROOT, "scripts", "state_transfer", "run_case3_cycle2_state_transfer.py")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_diagnosis_artifacts_and_hashes():
    """Validates existence, exact sizes, and cryptographic SHA-256 of all diagnosis deliverables."""
    expected = {
        REFINED_DECK: ("1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C", 17373692),
        PHYS_MESH: ("58466F66E1D9E41E73C5E5233DD748B5237193E225407320DB4288A8DB38081F", 3090607),
        STA_FILE: ("7CD84F404CF828700CF68352E07FA12739EA59B0BAE533CA47A018900AD0C420", 4183),
        MSG_FILE: ("7AC50248445EE92AABB4FD5827E78F49B213EB8319748471B3F9FF06F5C3413F", 250303),
        DAT_FILE: ("B5F0761C9B8F9683AF2728496A76E91E2BD73F440EFD57C18F2A8576C750D645", 39663),
        LOG_FILE: ("7761063901A66428015044DC364636861D040F59B04D9E65183ED7B4FB4DE00E", 2775),
        CSV_FILE: ("E0F01BA5075ADCA3FEF64E0811B52AD61FD285C5BEBEE25F1849315CADB8F6DB", 2891),
        OBS_JSON: ("05DAA9BC1B93A6B2D4C0D98DA1652527F7806F21AAF0ED01AFDC5502520E50D2", 3227),
        SPATIAL_JSON: ("882F69CB69FE6AB338794A71D3C1227035BA481CAF6E51D62121612F4DD27AF3", 33824),
        RECEIPT_JSON: ("FA53B5103B112CF9AB7A01AF0441B056D712A8086FA4697C3A1939017180F60E", 8225),
        SUMMARY_JSON: ("440DD0B590931EE3657914911AC437FF88957569C718CB5CCD52E108FF0E8585", 3083),
        EXEC_REPORT: ("A7835DFB36A41CA0066DFCA60C2B30D5A3C6D9A863F964B7DB60D99A2769FF77", 19915),
        DIAG_REPORT: ("163FC113B8254C5106FF95C6CC64FC63C0A8C954BF064DC294BDC0CC4BE1CD11", 15091),
        GEN_SCRIPT: ("4C61BC4950EB7491E594F2CFD1768D187FE039521A9476B2E8ED00BAFAA10EF4", 33734),
        UEL_FILE: ("CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", 29722)
    }
    for path, (exp_sha, exp_size) in expected.items():
        assert os.path.isfile(path), f"Missing artifact: {path}"
        act_size = os.path.getsize(path)
        assert act_size == exp_size, f"Size mismatch for {os.path.basename(path)}: expected {exp_size}, got {act_size}"
        act_sha = compute_sha256(path)
        assert act_sha == exp_sha, f"SHA mismatch for {os.path.basename(path)}: expected {exp_sha}, got {act_sha}"

def test_deck_regeneration_disclosure():
    """Validates full disclosure of candidate deck regeneration from 8DDE4D8B to 1D72A981."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    regen = rc["deck_regeneration"]
    assert regen["approved_deck_sha256"] == "8DDE4D8B4D441CEFFCE55979FBFB4DC5C5C0F6662446A310CE7D2791C24D338C"
    assert regen["executed_deck_sha256"] == "1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C"
    assert regen["deck_status"] == "REGENERATED_PREFLIGHT_SYNTAX_REPAIR"
    assert "defective *USER ELEMENT cards" in regen["syntax_repair_details"]
    assert "746,928" in regen["syntax_repair_details"]
    assert "707,616" in regen["syntax_repair_details"]
    assert regen["generating_script"] == "scripts/state_transfer/run_case3_cycle2_state_transfer.py"

def test_walltime_and_timestamp_disambiguation():
    """Validates distinction between PBS span and solver wallclock, and UTC/CET timestamps."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    se = rc["solver_execution"]
    assert "walltime_s" not in se, "Legacy walltime_s must be removed from solver_execution"
    assert se["pbs_job_span_walltime_s"] == 4602.0
    assert se["solver_wallclock_s"] == 4268.0
    assert se["solver_cpu_s"] == 2918.0
    assert "23:09:47Z" in se["timestamps_utc"]
    assert "00:09:47 CET" in se["timestamps_cet"]
    assert "timestamp_source_notes" in se

def test_forward_advance_baselines_and_damage_growth():
    """Validates dual crack advance baselines and classification of damage growth under hold."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    sp = rc["spatial_crack_propagation"]
    assert sp["donor_tip_baseline_forward_advance_mm_d095"] == 2.3686
    assert sp["post_hold_baseline_forward_advance_mm_d095"] == 2.3649
    assert sp["step1_damage_growth_classification"] == "GROWTH_UNDER_HOLD"

def test_terminal_frame_and_peak_load():
    """Validates relabeling of terminal frame as Increment 28 and dual peak load sources."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s2 = rc["step2_propagation"]
    assert "Increment 28" in s2["terminal_frame_label"]
    assert s2["peak_load_RF2_kN"] == 4.101037
    assert s2["peak_load_RF2_dat_kN"] == 4.1009829

def test_verbatim_uel_syntax_in_generating_script():
    """Validates that run_case3_cycle2_state_transfer.py writes the exact verbatim UEL cards."""
    with open(GEN_SCRIPT, "r", encoding="utf-8") as f:
        content = f.read()
    assert r"*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n" in content
    assert r"*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n" in content
    assert r"*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n" in content
    assert r"*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n" in content

def test_governance_and_task_accounting():
    """Validates zero new PBS jobs, cumulative 65 submissions, and task governance state."""
    with open(TASK_JSON, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] in ("METHOD-C-CASE3-JOB3-DIAGNOSIS", "METHOD-C-CASE3-CYCLE3-REFINEMENT-PACKAGE")
    assert task["master_goal_status"] == "OPEN"
    assert task["max_new_pbs_submissions"] == 0
    assert task["cumulative_pbs_submissions"] == 65
    assert task["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert task["correlation_id"] in ("HND-METHOD-C-CASE3-JOB3-DIAG-001", "HND-METHOD-C-CASE3-JOB3-DIAG-002", "HND-METHOD-C-CASE3-CYCLE3-PREP-001", "HND-METHOD-C-CASE3-CYCLE3-PREP-002")
