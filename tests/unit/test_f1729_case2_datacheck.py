# -*- coding: utf-8 -*-
# tests/unit/test_f1729_case2_datacheck.py
# Unit regression tests for Task F1729 Case 2 Companion Recovery HPC Abaqus Datacheck

import json
import os
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "results", "validation", "f1729_case2_datacheck_evidence")
SUMMARY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1729_case2_datacheck_summary.json")
REPORT_MD = os.path.join(REPO_ROOT, "docs", "validation", "F1729_CASE2_COMPANION_RECOVERY_DATACHECK_REPORT.md")
INP_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "220_f1729_case2_recovery_datacheck", "PK_HOLE_COMPANION_RECOVERY.inp")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1729_case2_datacheck_summary_all_gates_pass():
    assert os.path.isfile(SUMMARY_JSON), f"Summary JSON not found: {SUMMARY_JSON}"
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    assert data["task_id"] == "F1729-CASE2-COMPANION-RECOVERY-DATACHECK"
    assert data["job_id"] == "1423234.mmaster02"
    assert data["datacheck_status"] == "DATACHECK_EXIT_0_ALL_GATES_PASS"
    assert data["overall_pass"] is True
    
    gates = data["gate_results"]
    expected_gates = [
        "DC-01-SYNTAX-VALIDITY",
        "DC-02-ELEMENT-TOPOLOGY",
        "DC-03-MATERIAL-ASSIGNMENTS",
        "DC-04-BOUNDARY-CONDITIONS",
        "DC-05-OUTPUT-VARIABLES",
        "DC-06-EXIT-CODE-ZERO"
    ]
    for g in expected_gates:
        assert g in gates, f"Missing gate: {g}"
        assert gates[g] == "PASS", f"Gate failed: {g} = {gates[g]}"

def test_f1729_case2_datacheck_evidence_files_exist_and_hashes_match():
    assert os.path.isfile(SUMMARY_JSON)
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    evidence_hashes = data["evidence_hashes"]
    for filename, expected_hash in evidence_hashes.items():
        file_path = os.path.join(EVIDENCE_DIR, filename)
        assert os.path.isfile(file_path), f"Evidence file not found: {file_path}"
        actual_hash = sha256_file(file_path)
        assert actual_hash == expected_hash.upper(), f"Hash mismatch on {filename}: expected {expected_hash}, got {actual_hash}"

def test_f1729_case2_datacheck_pbs_execution_log():
    pbs_log = os.path.join(EVIDENCE_DIR, "pbs_execution.log")
    assert os.path.isfile(pbs_log)
    with open(pbs_log, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    assert "F1729_CASE2_DC" in content
    assert "mnode097.cluster" in content
    assert "0286f591f865e060d3c34482671d8e378916831d3781db17a4e8bc70963e51e0" in content.lower()
    assert "Datacheck Finished with Exit Code: 0" in content
    assert "Datacheck Verification Succeeded (Exit Code 0)" in content

def test_f1729_case2_datacheck_dat_file_diagnostics():
    dat_path = os.path.join(EVIDENCE_DIR, "PK_HOLE_COMPANION_RECOVERY_DC.dat")
    assert os.path.isfile(dat_path)
    with open(dat_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    assert "ANALYSIS DATACHECK COMPLETE" in content
    assert "NUMBER OF ELEMENTS IS                                  2906" in content
    assert "NUMBER OF NODES IS                                     3010" in content
    assert "TOTAL NUMBER OF VARIABLES IN THE MODEL                 6020" in content
    assert "***ERROR" not in content

def test_f1729_case2_companion_recovery_inp_no_uel_invoked():
    assert os.path.isfile(INP_PATH)
    with open(INP_PATH, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    assert "*USER ELEMENT" not in content.upper()
    assert "*UEL PROPERTY" not in content.upper()
    assert "CPE4" in content
    assert "CPE3" in content
    assert "MAT_BIN_INTACT" in content
    assert "MAT_BIN_SOFT_20" in content
