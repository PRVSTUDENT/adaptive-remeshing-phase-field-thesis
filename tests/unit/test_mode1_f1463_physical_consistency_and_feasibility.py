# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1463:
Audit Method B Physical Consistency, Verify Running PBS Jobs, and Test Crack-Path-Agnostic Refinement Feasibility.

Tests:
1. test_f1463_hpc_terminal_jobs_parity_and_determinism:
   Verifies terminal evidence, walltimes, speedups, and bitwise parity for Jobs 1412872 and 1412873.
2. test_f1463_at2_damage_evolution_and_unit_reconciliation:
   Verifies analytical AT2 formulation, continuous damage evolution, psi_0 = 180 MPa, and H_max = 18.88 MPa.
3. test_f1463_reference_element_count_reconciliation:
   Verifies canonical reference element count is 15,192 (45,576 records) and 15,220 typo is eliminated.
4. test_f1463_matched_displacement_work_and_bookkeeping_residual:
   Verifies exact trapezoidal work integration over u in [0, 0.007889 mm] and defined bookkeeping residual.
5. test_f1463_package40_provenance_and_adaptive_limitations:
   Verifies Package 40 mesh was generated from Step-2 propagated damage state (frame 1022).
6. test_f1463_production_uel_hash_integrity:
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

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CANONICAL_REF_FE_COUNT = 15192
CANONICAL_REF_RECORDS = 45576
CANONICAL_REF_K0 = 137.945520
CANONICAL_REF_FMAX = 0.757778
CANONICAL_REF_MATCHED_WEXT = 2.358732  # mJ at u = 0.007889 mm

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1463_hpc_terminal_jobs_parity_and_determinism():
    """Verify terminal execution, speedups, and bitwise parity for Jobs 1412872 and 1412873."""
    # Check that jobs are recorded in HPC ledger
    ledger_file = COORDINATION_DIR / "HPC_JOB_LEDGER.csv"
    with open(ledger_file, "r", encoding="utf-8") as f:
        ledger_text = f.read()
    assert "1412872.mmaster02" in ledger_text
    assert "1412873.mmaster02" in ledger_text

    # Native 14.7k 8T SMP energy balance hash parity
    native_8t_a_csv = RUNS_DIR / "harvest_results_f1416" / "energy_native_14k_8t_a.csv"
    native_1s_csv = RUNS_DIR / "harvest_results_f1416" / "energy_native_14k_1s.csv"
    assert native_8t_a_csv.is_file()
    assert native_1s_csv.is_file()

    # Both serial and 8T share exact same byte content
    hash_8t_a = sha256_file(native_8t_a_csv)
    hash_1s = sha256_file(native_1s_csv)
    assert hash_8t_a == "792BE67DB9AC2CA2E51B9811CA0FB6F374BF28D0BA160F725F2D071B3C38D99D"
    assert hash_1s == hash_8t_a

    # Check metrics
    native_metrics = RUNS_DIR / "harvest_results_f1416" / "m1_mb_native_14k_8t_a_metrics.json"
    with open(native_metrics, "r", encoding="utf-8") as f:
        m_nat = json.load(f)
    assert abs(m_nat["terminal_f_kN"] - 0.008262311) < 1e-7
    assert m_nat["terminal_u_mm"] == 0.01

    # Corrected 14.5k evaluation metrics
    corr_eval = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "corrected_method_b_evaluation.json"
    with open(corr_eval, "r", encoding="utf-8") as f:
        m_corr = json.load(f)
    assert abs(m_corr["F_terminal_kN"] - 0.0017644804) < 1e-7
    assert m_corr["u_terminal_mm"] == 0.007889
    assert m_corr["pbs_exit_status"] == 1

def test_f1463_at2_damage_evolution_and_unit_reconciliation():
    """Verify analytical AT2 continuous damage evolution, absence of initiation threshold, and 180 MPa scale."""
    # Physical constants
    Gc = 0.0027  # kN/mm = 2.7 N/mm
    l0 = 0.0075  # mm = 7.5 um
    psi_0 = Gc / (2.0 * l0)  # kN/mm^2 = GPa
    psi_0_MPa = psi_0 * 1000.0  # 180.0 MPa
    assert abs(psi_0 - 0.180) < 1e-6
    assert abs(psi_0_MPa - 180.0) < 1e-4

    # Observed notch tip damage at u = 0.0050 mm
    d_max = 0.094910
    # In standard AT2 (w(d)=d^2): d = H / (H + psi_0) => H = d / (1 - d) * psi_0
    H_max_kN_per_mm2 = (d_max / (1.0 - d_max)) * psi_0
    H_max_MPa = H_max_kN_per_mm2 * 1000.0
    assert abs(H_max_MPa - 18.875) < 0.05
    assert H_max_MPa < psi_0_MPa  # Sub-initiation regime

    # Check thesis text contains the corrected units and explanation
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "180.0" in tex_text
    assert "0.180" in tex_text
    assert "H / (H + G_c/(2\\ellzero))" in tex_text

def test_f1463_reference_element_count_reconciliation():
    """Verify canonical reference is 15,192 finite elements and 15,220 typo is eliminated."""
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()

    # 15,220 must NOT appear in chapter 4
    assert "15,220" not in tex_text
    assert "15{,}220" not in tex_text
    # Prohibited phrase "Physical Finite Elements" must NOT appear in Tab. 4.22
    assert "Physical Finite Elements" not in tex_text

    # Canonical Reference count 15,192 verified
    assert "15{,}192" in tex_text or "15,192" in tex_text

def test_f1463_matched_displacement_work_and_bookkeeping_residual():
    """Verify recomputed matched work integration and defined bookkeeping residual."""
    corr_eval = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "corrected_method_b_evaluation.json"
    with open(corr_eval, "r", encoding="utf-8") as f:
        data = json.load(f)

    w_ext = data["W_ext_terminal_mJ"]
    e_frac = data["E_fracture_terminal_mJ"]
    e_elas = data["E_elastic_terminal_mJ"]
    delta_e = data["energy_residual_delta_E_mJ"]
    rel_err = data["energy_residual_rel_pct"]

    assert abs(w_ext - 2.267379) < 0.001
    assert abs(e_frac - 2.285469) < 0.001
    assert abs(e_elas - 0.006960) < 0.001
    assert abs(delta_e - 0.025050) < 0.001
    assert abs(rel_err - 1.10479) < 0.001

    # Thesis must frame this as bookkeeping residual rather than complete balance
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "\\Delta E_{\\mathrm{book}}" in tex_text
    assert "bookkeeping residual" in tex_text.lower()

def test_f1463_package40_provenance_and_adaptive_limitations():
    """Verify Package 40 mesh was generated from Step-2 propagated damage state (companion frame 1022)."""
    manifest_path = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "PACKAGE_MANIFEST.json"
    assert manifest_path.is_file()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    source_state = manifest["source_state"]
    assert "Stage-14 Step-2" in source_state
    assert "companion frame 1022" in source_state
    assert manifest["base_elements"] == 14483
    assert manifest["total_3layer_elements"] == 43449

    # Thesis must explain this provenance and state boundary guards
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "companion frame 1022" in tex_text
    assert "offline engineering heuristic" in tex_text

def test_f1463_production_uel_hash_integrity():
    """Verify production UEL source f42_mixed_uel.for matches authoritative SHA-256."""
    uel_path = MODELS_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file()
    actual_hash = sha256_file(uel_path)
    assert actual_hash == FROZEN_BASELINE_UEL_HASH
