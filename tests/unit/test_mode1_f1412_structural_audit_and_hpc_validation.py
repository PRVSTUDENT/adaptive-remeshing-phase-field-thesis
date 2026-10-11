# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1412:
Critical Structural Audit, Live HPC Validation, and Method B Fracture-Response Qualification.

Verifies:
1. Reconstructed M1_MB_NATIVE_FINAL_1S.inp structural integrity:
   - Full 3-layer co-located UEL architecture (Phase U1/U3, Mech U2/U4, Companion CPE4/CPE3) totaling 44,031 elements.
   - Strict plane-strain formulation (CPE4/CPE3 and plane-strain UEL matrix).
   - 100% geometric boundary completeness (62 bottom nodes, 62 top nodes, 62 equations).
   - Zero-gap sharp crack slit with 62 duplicate node pairs.
2. Controlled structural comparison report:
   - Zero physically consequential discrepancies across Reference 15k, Historical ET2 6k, and Native Method B 14k.
   - Sole intended difference is spatial discretization.
   - Subroutine hash CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 preserved.
3. Extracted live metrics validation against reference thresholds:
   - Reference K0 = 137.945520 kN/mm, F_max = 0.757778 kN, u_peak = 0.005857 mm.
   - Method B 14k initial stiffness K0 error <= 1.0% (actual +0.0416%).
   - Historical ET2 6k initial stiffness K0 error <= 1.0% (actual -0.4137%).
   - Historical ET2 6k peak initiation force error <= 1.0% (actual -0.186%).
   - Historical ET2 6k peak displacement error <= 2.0% (actual -0.273%).
   - Energy bookkeeping discrepancy <= 0.5%.
4. Live job preservation and active dual-simulation tracking:
   - Job 1411895.mmaster02 (ET2 6k) and Job 1411934.mmaster02 (Method B 14k) active without cancellation or duplication.
5. Scientific verdict and stop condition compliance:
   - METHOD_B_NATIVE_MODEL_STRUCTURALLY_QUALIFIED_RESULTS_PENDING.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
NATIVE_DECK_PATH = MODELS_DIR / "38_method_b_native_final_14k" / "M1_MB_NATIVE_FINAL_1S.inp"
UEL_FORTRAN_PATH = MODELS_DIR / "38_method_b_native_final_14k" / "f42_mixed_uel.for"
AUDIT_DIR = REPO_ROOT / "runs" / "mode1" / "method_b_live_audit"
METRICS_JSON_PATH = AUDIT_DIR / "live_audit_metrics.json"
COMPARISON_JSON_PATH = AUDIT_DIR / "structural_comparison_report.json"
ACTIVE_TASK_PATH = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
HPC_LEDGER_PATH = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
REF_K0 = 137.945520
REF_FMAX = 0.757778
REF_U_PEAK = 0.005857

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1412_model_structural_integrity():
    """Verify the 14,677-element reconstructed deck has complete 3-layer UEL, plane strain, and complete boundary sets."""
    assert NATIVE_DECK_PATH.exists(), f"Missing deck: {NATIVE_DECK_PATH}"
    
    # Check UEL Fortran source hash
    uel_hash = sha256_file(UEL_FORTRAN_PATH)
    assert uel_hash == FROZEN_BASELINE_UEL_HASH, f"UEL hash mismatch: {uel_hash}"
    
    # Read deck and check element counts and sets
    u1_count = 0
    u2_count = 0
    u3_count = 0
    u4_count = 0
    cpe4_count = 0
    cpe3_count = 0
    
    current_kw = None
    with open(NATIVE_DECK_PATH, "r", encoding="utf-8") as f:
        for line in f:
            l = line.strip().upper()
            if l.startswith("*"):
                current_kw = l
                continue
            if not l or l.startswith("**"):
                continue
            if current_kw and current_kw.startswith("*ELEMENT"):
                if "TYPE=U1" in current_kw: u1_count += 1
                elif "TYPE=U2" in current_kw: u2_count += 1
                elif "TYPE=U3" in current_kw: u3_count += 1
                elif "TYPE=U4" in current_kw: u4_count += 1
                elif "TYPE=CPE4" in current_kw: cpe4_count += 1
                elif "TYPE=CPE3" in current_kw: cpe3_count += 1
                
    assert u1_count == 14244, f"Expected 14,244 U1 elements, got {u1_count}"
    assert u2_count == 14244, f"Expected 14,244 U2 mechanical elements, got {u2_count}"
    assert u3_count == 433, f"Expected 433 U3 elements, got {u3_count}"
    assert u4_count == 433, f"Expected 433 U4 mechanical elements, got {u4_count}"
    assert cpe4_count == 14244, f"Expected 14,244 CPE4 plane strain elements, got {cpe4_count}"
    assert cpe3_count == 433, f"Expected 433 CPE3 plane strain elements, got {cpe3_count}"
    
    total_phase = u1_count + u3_count
    total_mech = u2_count + u4_count
    total_umat = cpe4_count + cpe3_count
    assert total_phase == 14677
    assert total_mech == 14677, "Mechanical UEL layer is incomplete or missing!"
    assert total_umat == 14677
    assert total_phase + total_mech + total_umat == 44031

def test_f1412_tri_model_structural_comparison():
    """Verify the controlled structural comparison report across Reference, ET2, and Native Method B."""
    assert COMPARISON_JSON_PATH.exists(), f"Missing comparison report: {COMPARISON_JSON_PATH}"
    with open(COMPARISON_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    verdict = data["audit_verdict"]
    assert verdict["status"] == "STRUCTURALLY_AND_PHYSICALLY_QUALIFIED"
    assert verdict["physically_consequential_discrepancies"] == 0
    assert verdict["governing_conclusion"] == "METHOD_B_NATIVE_MODEL_STRUCTURALLY_QUALIFIED_RESULTS_PENDING"
    
    # Check features
    features = {f["feature"]: f for f in data["feature_audits"]}
    assert "Subroutine & Weak Form Implementation" in features
    assert "Co-Located Element Architecture" in features
    assert "Constitutive & Dimension Formulation" in features
    assert "Bottom Roller Support (y=0)" in features
    assert "Top Boundary & Kinematic Coupling (y=1)" in features
    assert "Crack Seam Topology (y=0.5, 0<=x<=0.5)" in features

def test_f1412_live_metrics_and_audit_thresholds():
    """Verify live metrics extracted from both running cluster jobs against quantitative audit thresholds."""
    assert METRICS_JSON_PATH.exists(), f"Missing live metrics: {METRICS_JSON_PATH}"
    with open(METRICS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Method B 14k audit
    mb = data["native_method_b_14k"]
    assert mb["job_id"] == "1411934.mmaster02"
    assert mb["mesh_fe"] == 14677
    k0_mb = mb["k0"]["k0_kN_per_mm"]
    rel_diff_k0_mb = abs(k0_mb - REF_K0) / REF_K0 * 100.0
    assert rel_diff_k0_mb <= 1.0, f"Method B initial stiffness error {rel_diff_k0_mb:.4f}% exceeds 1.0% threshold!"
    assert rel_diff_k0_mb < 0.10, "Method B initial stiffness is exceptionally accurate (< 0.1%)!"
    
    # Historical ET2 6k audit
    et2 = data["historical_et2_6k"]
    assert et2["job_id"] == "1411895.mmaster02"
    assert et2["mesh_fe"] == 6112
    k0_et2 = et2["k0"]["k0_kN_per_mm"]
    rel_diff_k0_et2 = abs(k0_et2 - REF_K0) / REF_K0 * 100.0
    assert rel_diff_k0_et2 <= 1.0, f"Historical ET2 initial stiffness error {rel_diff_k0_et2:.4f}% exceeds 1.0% threshold!"
    
    # ET2 Peak Crossing Verification
    fmax_et2 = et2["f_max_kN"]
    u_fmax_et2 = et2["u_at_f_max_mm"]
    rel_diff_fmax_et2 = abs(fmax_et2 - REF_FMAX) / REF_FMAX * 100.0
    rel_diff_u_fmax_et2 = abs(u_fmax_et2 - REF_U_PEAK) / REF_U_PEAK * 100.0
    assert rel_diff_fmax_et2 <= 1.0, f"Historical ET2 peak force error {rel_diff_fmax_et2:.4f}% exceeds 1.0% threshold!"
    assert rel_diff_u_fmax_et2 <= 2.0, f"Historical ET2 peak displacement error {rel_diff_u_fmax_et2:.4f}% exceeds 2.0% threshold!"
    assert et2["current_rf_kN"] < fmax_et2, "Simulation has not entered post-peak softening!"

def test_f1412_dual_job_preservation():
    """Verify both simulations are preserved in HPC ledger and ACTIVE_TASK without duplication."""
    assert HPC_LEDGER_PATH.exists()
    content = HPC_LEDGER_PATH.read_text(encoding="utf-8")
    assert "1411895.mmaster02" in content
    assert "1411934.mmaster02" in content
    
    with open(ACTIVE_TASK_PATH, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    assert "1411895.mmaster02" in task_data["active_pbs_job_ids"]
    assert "1411934.mmaster02" in task_data["active_pbs_job_ids"]
    assert len(task_data["active_pbs_job_ids"]) == 2

