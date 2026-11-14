# -*- coding: utf-8 -*-
"""
test_f1740_case3_multistate_design.py
Unit tests validating Task F1740 Case 3 Multi-State Error-Indicator Envelope Feasibility & Technical Design.
"""

import os
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_frozen_uel_sha256():
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "227_f1739_case1_adapted_fracture", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), f"UEL file missing: {uel_path}"
    with open(uel_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest().upper()
    EXPECTED_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert digest == EXPECTED_SHA, f"Frozen UEL SHA-256 mismatch: {digest} vs {EXPECTED_SHA}"

def test_task192_donor_checkpoints_exist():
    donor_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
    assert os.path.isdir(donor_dir), f"Donor dir missing: {donor_dir}"
    
    # Check key donor artifacts
    job1_dat = os.path.join(donor_dir, "PK_SEC43_STAGGERED_JOB1.dat")
    audit_json = os.path.join(donor_dir, "f1692_sec43_damage_and_miseseri_audit.json")
    sec_midprop_inp = os.path.join(donor_dir, "PK_SEC43_STAGGERED_RECOVERY_SEC_MIDPROP.inp")
    
    assert os.path.exists(job1_dat) and os.path.getsize(job1_dat) > 100000
    assert os.path.exists(audit_json) and os.path.getsize(audit_json) > 10000
    assert os.path.exists(sec_midprop_inp) and os.path.getsize(sec_midprop_inp) > 100000

def test_base_physical_mesh_element_count():
    phys_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "PK_SEC43_STAGGERED_PHYS.inp")
    assert os.path.exists(phys_inp), f"Base mesh missing: {phys_inp}"
    
    cpe3_count = 0
    cpe4_count = 0
    with open(phys_inp, "r") as f:
        current_type = None
        for line in f:
            line_s = line.strip().upper()
            if line_s.startswith("*ELEMENT"):
                if "CPE3" in line_s:
                    current_type = "CPE3"
                elif "CPE4" in line_s:
                    current_type = "CPE4"
                else:
                    current_type = None
                continue
            elif line_s.startswith("*"):
                current_type = None
                continue
            if current_type == "CPE3":
                cpe3_count += 1
            elif current_type == "CPE4":
                cpe4_count += 1
                
    total_elems = cpe3_count + cpe4_count
    assert total_elems == 3923, f"Expected 3,923 elements, found {total_elems}"
    assert cpe4_count == 3814, f"Expected 3,814 CPE4 quads, found {cpe4_count}"
    assert cpe3_count == 109, f"Expected 109 CPE3 tris, found {cpe3_count}"
    pct_quads = (cpe4_count / total_elems) * 100.0
    assert pct_quads >= 97.0, f"Expected quad percentage >= 97%, found {pct_quads:.2f}%"

def test_corridor_geometric_definitions():
    # Case 3 geometry check
    # Notch: (10.0, 70.0), Hole left: (26.5, 51.0), Hole right: (46.5, 51.0), Edge: (65.0, 52.0)
    l0 = 0.285 # mm
    dx1 = 26.5 - 10.0
    dy1 = 51.0 - 70.0
    L1 = (dx1**2 + dy1**2)**0.5
    assert abs(L1 - 25.164) < 0.01, f"Primary corridor length mismatch: {L1}"
    assert L1 / l0 > 80.0, f"Expected L1/l0 > 80, found {L1/l0}"
    
    dx2 = 65.0 - 46.5
    dy2 = 52.0 - 51.0
    L2 = (dx2**2 + dy2**2)**0.5
    assert abs(L2 - 18.527) < 0.01, f"Secondary corridor length mismatch: {L2}"
    assert L2 / l0 > 60.0, f"Expected L2/l0 > 60, found {L2/l0}"

def test_design_report_contains_all_seven_gates():
    report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1740_CASE3_MULTISTATE_ENVELOPE_DESIGN_REPORT.md")
    assert os.path.exists(report_path), f"Report missing: {report_path}"
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    for g in ["Gate 3-01", "Gate 3-02", "Gate 3-03", "Gate 3-04", "Gate 3-05", "Gate 3-06", "Gate 3-07"]:
        assert g in content, f"Missing {g} in design report"

def test_design_report_addresses_all_findings_f1740_r01_to_r08():
    report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1740_CASE3_MULTISTATE_ENVELOPE_DESIGN_REPORT.md")
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    for r in ["F1740-R01", "F1740-R02", "F1740-R03", "F1740-R04", "F1740-R05", "F1740-R06", "F1740-R07", "F1740-R08"]:
        assert r in content, f"Missing review finding resolution for {r}"

def test_case3_envelope_donor_summary():
    summary_path = os.path.join(REPO_ROOT, "results", "validation", "f1740_case3_envelope_donor_summary.json")
    assert os.path.exists(summary_path), f"Summary missing: {summary_path}"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["element_count"] == 3923
    assert summary["primary_dominated_elements"] + summary["secondary_dominated_elements"] == 3923
    assert summary["primary_dominated_elements"] > 1000
    assert summary["secondary_dominated_elements"] > 1000
    assert summary["reference_stress_S_ref_MPa"] == 100.0

def test_case3_envelope_donor_odb_exists():
    odb_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state", "PK_SEC43_MULTISTATE_ENVELOPE_DONOR.odb")
    assert os.path.exists(odb_path), f"Envelope ODB missing: {odb_path}"
    assert os.path.getsize(odb_path) > 1000000

def test_accounting_and_ledger_integrity():
    task_json_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json_path, "r", encoding="utf-8-sig") as f:
        task_data = json.load(f)
    assert task_data["task_id"] in ["F1740-CASE3-MULTISTATE-ENVELOPE-DESIGN", "F1741-CASE3-MULTISTATE-REMESHING-EXECUTION"]
    assert task_data["cumulative_pbs_submissions"] in [17, 18]
    assert task_data["submissions_consumed"] in [0, 1, 2]
    assert "1423321.mmaster02" in task_data["historical_pbs_job_ids"]
