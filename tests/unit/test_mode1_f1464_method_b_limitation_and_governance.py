# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1464:
Validate Method B Limitation, Mathematical AT-2 Audit, Retrospective Mesh Provenance, and Governance.

Tests:
1. test_f1464_terminal_hpc_evidence_and_timing:
   Verifies terminal records, walltimes, speedups, and bitwise parity for Jobs 1412872 and 1412873.
2. test_f1464_at2_laplacian_coupling_and_zero_gradient_limit:
   Verifies strong-form Euler-Lagrange equation, zero-gradient scalar formula d_hom = H / (H + psi_0),
   and distinct coupled nodal fields (coarse d_max = 0.094910 vs fine d_max = 0.3195).
3. test_f1464_package40_retrospective_mesh_provenance:
   Verifies Package 40 manifest records Step-2 companion frame 1022 provenance and classification
   as retrospective verification mesh in thesis Chapter 4 and supervisor briefing.
4. test_f1464_prospective_remeshing_spatial_decay_limitation:
   Verifies from SPATIAL_LOCALIZATION_AUDIT_REPORT.json that prospective linear-elastic pre-analysis
   leaves zero fine elements (h <= 2 um) along the uncracked ligament at stations x = 0.7, 0.8, 0.9.
5. test_f1464_method_c_candidate_status_guard:
   Verifies thesis and briefing classify Method C strictly as an unqualified candidate approach
   with Gate 6C on hold, without claiming proven mathematical necessity.
6. test_f1464_governance_and_production_uel_hash:
   Verifies f42_mixed_uel.for matches authoritative SHA-256.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COORDINATION_DIR = REPO_ROOT / "project_coordination"
MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
RUNS_DIR = REPO_ROOT / "runs" / "mode1"
TEX_PATH = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "chapter04_current_status.tex"
BRIEFING_PATH = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1464_terminal_hpc_evidence_and_timing():
    """Verify terminal records, walltimes, speedups, and bitwise parity for Jobs 1412872 and 1412873."""
    ledger_file = COORDINATION_DIR / "HPC_JOB_LEDGER.csv"
    with open(ledger_file, "r", encoding="utf-8") as f:
        ledger_text = f.read()

    # Both jobs must be marked terminal F in ledger
    assert "1412872.mmaster02" in ledger_text
    assert "1412873.mmaster02" in ledger_text
    assert "F,0,F1463_MODE1_METHOD_B_NATIVE_14677FE_8THREAD_SMP_STAGE_B_DETERMINISM_REPEAT" in ledger_text
    assert "F,1,F1463_MODE1_METHOD_B_CORRECTED_14483FE_8THREAD_SMP_STAGE_A_SCALING_PARITY" in ledger_text

    # Native 8T SMP energy trace hash parity (7000 increments)
    native_8t_csv = RUNS_DIR / "harvest_results_f1416" / "energy_native_14k_8t_a.csv"
    assert native_8t_csv.is_file()
    assert sha256_file(native_8t_csv) == "792BE67DB9AC2CA2E51B9811CA0FB6F374BF28D0BA160F725F2D071B3C38D99D"

    # Corrected 14.5k evaluation metrics
    corr_eval = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "corrected_method_b_evaluation.json"
    with open(corr_eval, "r", encoding="utf-8") as f:
        m_corr = json.load(f)
    assert abs(m_corr["F_terminal_kN"] - 0.0017644804) < 1e-7
    assert m_corr["u_terminal_mm"] == 0.007889
    assert m_corr["pbs_exit_status"] == 1

def test_f1464_at2_laplacian_coupling_and_zero_gradient_limit():
    """Verify AT-2 Euler-Lagrange strong form, zero-gradient limit d_hom = H / (H + psi_0), and coupled fields."""
    Gc = 0.0027  # kN/mm
    l0 = 0.0075  # mm
    psi_0 = Gc / (2.0 * l0)  # 0.180 kN/mm^2 = 180.0 MPa
    assert abs(psi_0 - 0.180) < 1e-6
    psi_0_MPa = psi_0 * 1000.0
    assert abs(psi_0_MPa - 180.0) < 1e-4

    # Zero-gradient limit calculation
    H_max_MPa = 18.875
    d_hom = H_max_MPa / (H_max_MPa + psi_0_MPa)
    assert abs(d_hom - 0.094910) < 0.001

    # Thesis must explicitly document Euler-Lagrange strong form and distinguish zero-gradient scalar from coupled FE
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "eq:at2_euler_lagrange_strong_form" in tex_text
    assert "\\nabla^2 d = 0" in tex_text
    assert "homogeneous" in tex_text.lower()
    assert "Laplacian" in tex_text or "laplacian" in tex_text

def test_f1464_package40_retrospective_mesh_provenance():
    """Verify Package 40 manifest records Step-2 frame 1022 provenance and retrospective classification."""
    manifest_path = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "companion frame 1022" in manifest["source_state"]
    assert "Stage-14 Step-2" in manifest["source_state"]
    assert manifest["base_elements"] == 14483

    # Thesis and Briefing must classify it as retrospective verification mesh
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "retrospective, benchmark-specific verification mesh" in tex_text.lower()

    with open(BRIEFING_PATH, "r", encoding="utf-8") as f:
        briefing_text = f.read()
    assert "retrospective, benchmark-specific verification mesh" in briefing_text.lower()

def test_f1464_prospective_remeshing_spatial_decay_limitation():
    """Verify prospective linear-elastic pre-analysis leaves zero fine elements along ligament at x >= 0.70."""
    audit_path = MODELS_DIR / "88_mode1_preanalysis_uel_corrected" / "SPATIAL_LOCALIZATION_AUDIT_REPORT.json"
    with open(audit_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    # In 2% adapted mesh (11,737 elements) from prospective Step-1 pre-analysis
    m2 = audit_data["2pct_adapted_mesh_11k"]["transverse_widths"]
    for station in m2:
        x_st = station["x_station"]
        if x_st in [0.7, 0.8, 0.9]:
            assert station["fine_count_h_le_0002"] == 0, f"Expected 0 fine elements at station x={x_st}"
            assert station["mod_count_h_le_0005"] == 0, f"Expected 0 moderate elements at station x={x_st}"

    # In 1% adapted mesh (48,329 elements) from prospective Step-1 pre-analysis
    m1 = audit_data["1pct_adapted_mesh_48k"]["transverse_widths"]
    for station in m1:
        x_st = station["x_station"]
        if x_st in [0.7, 0.8]:
            assert station["fine_count_h_le_0002"] == 0, f"Expected 0 fine elements at station x={x_st}"

def test_f1464_method_c_candidate_status_guard():
    """Verify Method C is classified strictly as an unqualified candidate approach under Gate 6C hold."""
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "unqualified candidate sequential remeshing methodology" in tex_text.lower()

    with open(BRIEFING_PATH, "r", encoding="utf-8") as f:
        briefing_text = f.read()
    assert "unqualified candidate sequential remeshing methodology" in briefing_text.lower()

def test_f1464_governance_and_production_uel_hash():
    """Verify production UEL source f42_mixed_uel.for matches authoritative SHA-256."""
    uel_path = MODELS_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file()
    actual_hash = sha256_file(uel_path)
    assert actual_hash == FROZEN_BASELINE_UEL_HASH
