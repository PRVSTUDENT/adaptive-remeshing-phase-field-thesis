# -*- coding: utf-8 -*-
"""
tests/unit/test_f1743_case3_transient_companion.py
==================================================
Unit regression suite for Task F1743: Case 3 Transient Propagation Companion
Stress-Recovery & Native MISESERI Generation.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "229_f1743_case3_transient_recovery")
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
EXTRACTED_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1743_extracted_transient_uel.json")
SUMMARY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1743_companion_recovery_summary.json")
PBS_LOG = os.path.join(PKG_DIR, "pbs_execution.log")
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_f1743_active_task_governance():
    assert os.path.exists(ACTIVE_TASK_JSON)
    with open(ACTIVE_TASK_JSON, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] in [
        "F1743-CASE3-TRANSIENT-COMPANION-RECOVERY",
        "F1744-CASE3-5STATE-REMESHING-EXECUTION",
        "F1745-CASE3-5STATE-ENVELOPE-QUALIFICATION",
        "F1746-CASE3-5STATE-ENVELOPE-EXECUTION",
        "F1747-CASE3-CONTRAST-TRANSFORMATION-PROTOTYPE"
    ]
    assert task["frozen_uel_sha256"].lower() == FROZEN_UEL_SHA
    if task["task_id"] == "F1743-CASE3-TRANSIENT-COMPANION-RECOVERY":
        assert task["max_new_pbs_submissions"] <= 1
        assert task["cumulative_pbs_submissions"] in (19, 20)
        assert len(task["historical_pbs_job_ids"]) in (19, 20)
    else:
        assert task["cumulative_pbs_submissions"] >= 20
        assert len(task["historical_pbs_job_ids"]) >= 20
    assert any(x in task["scope_boundary"] for x in [
        "BOUNDED_1CPU_SERIAL_COMPANION_RECOVERY",
        "BOUNDED_5STATE_SEQUENTIAL_NATIVE_REMESHING",
        "ZERO_PBS_OFFLINE_5STATE_ENVELOPE_QUALIFICATION_AND_RECONCILIATION",
        "BOUNDED_1PASS_5STATE_ENVELOPE_NATIVE_REMESHING",
        "ZERO_PBS_GEOMETRY_INDEPENDENT_CONTRAST_PROTOTYPE"
    ])

def test_f1743_package_manifest():
    manifest_path = os.path.join(PKG_DIR, "f1743_case3_transient_recovery.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["task_id"] == "F1743-CASE3-TRANSIENT-COMPANION-RECOVERY"
    assert m["benchmark_case"] == "Case 3"
    assert "T1" in m["states"]
    assert "T2" in m["states"]
    assert "T3" in m["states"]
    assert m["governance"]["forward_fracture_simulation"] is False
    assert m["governance"]["production_remeshing"] is False
    assert m["governance"]["geometric_track_hardcoding"] is False

def test_f1743_extracted_transient_data_provenance():
    assert os.path.exists(EXTRACTED_JSON)
    with open(EXTRACTED_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    for key in ("INC_260", "INC_300", "INC_340"):
        assert key in data
        item = data[key]
        assert len(item["nodal_displacements"]) == 4040
        assert len(item["element_avg_damage"]) == 3923
        assert item["d_max"] >= 0.9980
        assert item["broken_elements_count"] >= 15
    # Monotonic crack growth across sampled frames
    b1 = data["INC_260"]["broken_elements_count"]
    b2 = data["INC_300"]["broken_elements_count"]
    b3 = data["INC_340"]["broken_elements_count"]
    assert b1 < b2 <= b3, f"Expected monotonic increase in broken elements: {b1} < {b2} <= {b3}"

def test_f1743_companion_inp_decks():
    decks = [
        "PK_SEC43_COMPANION_T1.inp",
        "PK_SEC43_COMPANION_T2.inp",
        "PK_SEC43_COMPANION_T3.inp"
    ]
    for d in decks:
        path = os.path.join(PKG_DIR, d)
        assert os.path.exists(path), f"Deck missing: {path}"
        assert os.path.getsize(path) > 400000
        with open(path, "r") as f:
            content = f.read()
        assert "*ELASTIC, DEPENDENCIES=1" in content
        assert "*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1" in content
        assert "MISESERI, MISESAVG" in content
        assert "*ELEMENT, TYPE=CPE4" in content
        assert "*ELEMENT, TYPE=CPE3" in content
        assert "*STEP, NAME=RECOVERY" in content

def test_f1743_pbs_script_preflight_and_notifications():
    pbs_path = os.path.join(PKG_DIR, "submit_f1743_case3_transient_recovery.pbs")
    assert os.path.exists(pbs_path)
    with open(pbs_path, "r") as f:
        text = f.read()
    assert "#PBS -m abe" in text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in text
    assert "#PBS -l select=1:ncpus=1:mem=8gb" in text
    assert "f42_mixed_uel.for" in text
    assert FROZEN_UEL_SHA in text
    assert "job_notifications.sh" in text
    assert "audit_f1743_companion_fields.py" in text

def test_f1743_companion_recovery_execution_results():
    assert os.path.exists(SUMMARY_JSON), f"Summary JSON missing: {SUMMARY_JSON}"
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["audit_pass"] is True
    states = summary["companion_states"]
    for sid in ("T1", "T2", "T3"):
        assert sid in states
        s = states[sid]
        assert s["has_miseseri"] is True
        assert s["has_misesavg"] is True
        assert s["miseseri_max"] > 1.5
        assert s["misesavg_max"] > 3.0
        assert s["num_elements"] == 3923
        # Static equilibrium residual < 1e-6 kN
        rf = s["rf_net_sum_kN"]
        assert abs(rf[0]) < 1.0e-6
        assert abs(rf[1]) < 1.0e-6

    # Verify monotonic increase of MISESERI peak with crack advance
    eri1 = states["T1"]["miseseri_max"]
    eri2 = states["T2"]["miseseri_max"]
    eri3 = states["T3"]["miseseri_max"]
    assert eri1 < eri2 < eri3, f"Expected increasing error intensity: {eri1} < {eri2} < {eri3}"

def test_f1743_pbs_execution_log_cleanliness():
    assert os.path.exists(PBS_LOG), f"PBS log missing: {PBS_LOG}"
    with open(PBS_LOG, "r", encoding="utf-8") as f:
        log_text = f.read()
    assert "exit code 0" in log_text
    assert "Produced PK_SEC43_COMPANION_T1.odb" in log_text
    assert "Produced PK_SEC43_COMPANION_T2.odb" in log_text
    assert "Produced PK_SEC43_COMPANION_T3.odb" in log_text
    assert "All 3 Companion Recovery Checkpoints Solved and Audited Cleanly" in log_text
