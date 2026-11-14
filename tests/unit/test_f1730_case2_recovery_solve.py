# -*- coding: utf-8 -*-
# tests/unit/test_f1730_case2_recovery_solve.py
# Unit regression tests for Task F1730 Case 2 Companion Degraded Cauchy Stress Recovery HPC Solve & MISESERI Audit

import json
import os
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "results", "validation", "f1730_case2_recovery_evidence")
SUMMARY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1730_case2_recovery_solve_summary.json")
TELEMETRY_JSON = os.path.join(EVIDENCE_DIR, "f1730_case2_recovery_telemetry.json")
REPORT_MD = os.path.join(REPO_ROOT, "docs", "validation", "F1730_CASE2_COMPANION_RECOVERY_SOLVE_REPORT.md")
INP_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "221_f1730_case2_recovery_solve", "PK_HOLE_COMPANION_RECOVERY.inp")
PBS_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "221_f1730_case2_recovery_solve", "submit_f1730_case2_recovery_solve.pbs")
EXTRACT_PY = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "221_f1730_case2_recovery_solve", "extract_case2_recovery_miseseri.py")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1730_staged_artifacts_exist_and_hashes_valid():
    assert os.path.isfile(INP_PATH), f"INP missing: {INP_PATH}"
    assert os.path.isfile(PBS_PATH), f"PBS script missing: {PBS_PATH}"
    assert os.path.isfile(EXTRACT_PY), f"Extraction script missing: {EXTRACT_PY}"
    assert os.path.isfile(REPORT_MD), f"Report missing: {REPORT_MD}"
    
    inp_sha = sha256_file(INP_PATH)
    assert inp_sha == "0286F591F865E060D3C34482671D8E378916831D3781DB17A4E8BC70963E51E0"

def test_f1730_inp_deck_is_pure_continuum_no_uel():
    with open(INP_PATH, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    assert "*USER ELEMENT" not in content.upper()
    assert "*UEL PROPERTY" not in content.upper()
    assert "CPE4" in content
    assert "CPE3" in content
    assert "MAT_BIN_INTACT" in content
    assert "MAT_BIN_SOFT_20" in content

def test_f1730_pbs_script_directives_and_gates():
    with open(PBS_PATH, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    assert "#PBS -N F1730_CASE2_SOLVE" in content
    assert "PK_HOLE_COMPANION_RECOVERY.inp" in content
    assert "0286f591f865e060d3c34482671d8e378916831d3781db17a4e8bc70963e51e0" in content.lower()
    assert "abaqus job=" in content
    assert "extract_case2_recovery_miseseri.py" in content
    assert "job_notifications.sh" in content

def test_f1730_solve_summary_all_gates_pass():
    assert os.path.isfile(SUMMARY_JSON), f"Summary JSON not found: {SUMMARY_JSON}"
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        
    assert data["task_id"] == "F1730-CASE2-COMPANION-RECOVERY-SOLVE"
    assert data["solve_status"] == "RECOVERY_SOLVE_EXIT_0_ALL_7_GATES_PASS"
    assert data["overall_pass"] is True
    assert data["job_id"] == "1423235.mmaster02"
    
    gates = data["gate_results"]
    expected_gates = [
        "SOLVE-01-CONVERGED-INCREMENT",
        "SOLVE-02-VERTICAL-EQUILIBRIUM",
        "SOLVE-03-REACTION-FORCE-REPORTED",
        "SOLVE-04-FIELDS-POPULATED",
        "SOLVE-05-FINITE-COVERAGE",
        "SOLVE-06-PROCESS-ZONE-CONTRAST",
        "SOLVE-07-WARNINGS-CLASSIFIED"
    ]
    for g in expected_gates:
        assert g in gates, f"Missing gate: {g}"
        assert gates[g] == "PASS", f"Gate failed: {g} = {gates[g]}"

def test_f1730_telemetry_force_equilibrium_and_contrast():
    assert os.path.isfile(TELEMETRY_JSON), f"Telemetry JSON not found: {TELEMETRY_JSON}"
    with open(TELEMETRY_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        
    # Equilibrium
    rf = data["reaction_forces"]
    assert rf["vertical_equilibrium_pass"] is True
    assert rf["relative_vertical_residual"] <= 1.0e-4
    assert rf["relative_vertical_residual"] < 1.0e-7  # actual is ~9e-9
    assert abs(rf["top_rf_y_kn"] - 0.715238) < 1.0e-3
    assert abs(rf["bottom_rf_y_kn"] + 0.715238) < 1.0e-3
    assert rf["original_coupled_peak_force_kn"] == 0.731015
    
    # Contrast
    ind = data["error_indicator_statistics"]
    assert ind["contrast_threshold_pass"] is True
    assert ind["contrast_damaged_vs_bulk"] >= 5.0
    assert ind["contrast_damaged_vs_bulk"] > 12.0  # actual is ~12.67x
    assert ind["contrast_boundary_ligament_vs_bulk"] >= 5.0
    assert ind["contrast_boundary_ligament_vs_bulk"] > 8.0  # actual is ~8.50x
    assert ind["damaged_elements_count"] == 48
    assert ind["bulk_elements_count"] == 2858
    assert ind["boundary_ligament_count"] == 6
    
    # Coverage
    cov = data["mesh_coverage"]
    assert cov["total_elements"] == 2906
    assert cov["expected_elements"] == 2906
    assert cov["finite_coverage_pct"] == 100.0
    assert cov["non_finite_count"] == 0
    assert cov["zero_error_count"] == 0

def test_f1730_evidence_files_exist_and_hashes_match():
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        
    for fname, expected_sha in data["evidence_hashes"].items():
        fpath = os.path.join(EVIDENCE_DIR, fname)
        assert os.path.isfile(fpath), f"Evidence file not found: {fpath}"
        actual_sha = sha256_file(fpath)
        assert actual_sha == expected_sha.upper(), f"Hash mismatch on {fname}"
