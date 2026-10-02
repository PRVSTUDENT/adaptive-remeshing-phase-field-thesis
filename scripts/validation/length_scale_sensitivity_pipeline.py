#!/usr/bin/env python3
"""
scripts/validation/length_scale_sensitivity_pipeline.py

Phase-Field Length-Scale Sensitivity / Characterization Pipeline
================================================================

Implements the multi-quantity sensitivity analysis pipeline for the Gate-6B
Mode-I phase-field regularized length-scale series (L1, L2, L3):
  - L1: l0 = 0.0075 mm (7.5 um), h = 1.5 um, h/l0 = 0.200 (Baseline anchor)
  - L2: l0 = 0.01125 mm (11.25 um), h = 1.5 um, h/l0 = 0.133 (1.5x l0)
  - L3: l0 = 0.01500 mm (15.0 um), h = 1.5 um, h/l0 = 0.100 (2.0x l0)

Governed Terminology Rule:
  This branch is formally designated as "phase-field length-scale sensitivity /
  characterization", NOT "length-scale convergence", because varying l0 modifies
  the continuum fracture regularization parameter rather than the numerical
  discretization.

Anchor Equivalence Rule:
  L1_BASELINE = REUSE_S3_REFERENCE (Candidate L1 is mathematically identical to S3).

Authoritative Gate-6B Production UEL:
  f42_mixed_uel.for (SHA-256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6)
"""

import os
import sys
import re
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# Canonical constants
E_MODULUS = 210.0  # kN/mm^2 (GPa)
NU_POISSON = 0.3
G_CRITICAL = 0.0027  # kN/mm (kJ/m^2)
K_RESIDUAL = 1.0e-7
T_REF_MM = 1.0  # mm slice convention
NPHYS_S3 = 41912.0

LENGTH_SCALE_CANDIDATES = {
    "L1": {
        "candidate_id": "L1",
        "role": "phase_field_length_scale_sensitivity_baseline",
        "l0_mm": 0.0075,
        "l0_um": 7.5,
        "ratio_label": "1.0x_baseline",
        "h_mm": 0.0015,
        "h_over_l0": 0.200,
        "n_elements": 41912,
        "n_nodes": 42364,
        "package_dir": "models/pandey_kumar_mode1/20_length_scale_l1_baseline",
        "deck_filename": "PK_MODE1_L1_BASELINE_ENERGY.inp",
        "is_baseline_s3": True,
        "s3_reference_package": "models/pandey_kumar_mode1/13_fixed_convergence_h0015",
        "s3_reference_deck": "PK_MODE1_FIX_H0015_ENERGY.inp",
        "historical_job": "1406017.mmaster02"
    },
    "L2": {
        "candidate_id": "L2",
        "role": "phase_field_length_scale_sensitivity_intermediate",
        "l0_mm": 0.01125,
        "l0_um": 11.25,
        "ratio_label": "1.5x_intermediate",
        "h_mm": 0.0015,
        "h_over_l0": 0.1333,
        "n_elements": 41912,
        "n_nodes": 42364,
        "package_dir": "models/pandey_kumar_mode1/21_length_scale_l2_intermediate",
        "deck_filename": "PK_MODE1_L2_L01125_ENERGY.inp",
        "is_baseline_s3": False,
        "historical_job": "1406895.mmaster02"
    },
    "L3": {
        "candidate_id": "L3",
        "role": "phase_field_length_scale_sensitivity_coarse",
        "l0_mm": 0.01500,
        "l0_um": 15.0,
        "ratio_label": "2.0x_coarse",
        "h_mm": 0.0015,
        "h_over_l0": 0.100,
        "n_elements": 41912,
        "n_nodes": 42364,
        "package_dir": "models/pandey_kumar_mode1/22_length_scale_l3_coarse",
        "deck_filename": "PK_MODE1_L3_L01500_ENERGY.inp",
        "is_baseline_s3": False,
        "historical_job": "1406896.mmaster02"
    }
}


def compute_sha256(filepath: str) -> str:
    """Compute uppercase SHA256 of file."""
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


def verify_l1_s3_equivalence(base_workspace: str = ".") -> Dict[str, Any]:
    """
    Perform line-by-line semantic and model equivalence audit between Candidate L1
    and staged Candidate S3 reference deck.
    
    Verifies that L1 is mathematically and physically identical to S3, establishing:
      L1_BASELINE = REUSE_S3_REFERENCE
    """
    s3_deck_path = os.path.join(
        base_workspace, "models", "pandey_kumar_mode1", "13_fixed_convergence_h0015", "PK_MODE1_FIX_H0015_ENERGY.inp"
    )
    l1_deck_path = os.path.join(
        base_workspace, "models", "pandey_kumar_mode1", "20_length_scale_l1_baseline", "PK_MODE1_L1_BASELINE_ENERGY.inp"
    )
    
    if not os.path.exists(s3_deck_path) or not os.path.exists(l1_deck_path):
        return {
            "status": "ERROR_FILES_MISSING",
            "s3_exists": os.path.exists(s3_deck_path),
            "l1_exists": os.path.exists(l1_deck_path)
        }
        
    with open(s3_deck_path, "r", encoding="utf-8", errors="ignore") as f:
        s3_lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("**")]
        
    with open(l1_deck_path, "r", encoding="utf-8", errors="ignore") as f:
        l1_lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("**")]
        
    differences = []
    max_len = max(len(s3_lines), len(l1_lines))
    for i in range(max_len):
        line_s3 = s3_lines[i] if i < len(s3_lines) else "<EOF>"
        line_l1 = l1_lines[i] if i < len(l1_lines) else "<EOF>"
        if line_s3 != line_l1:
            differences.append({
                "non_comment_line": i + 1,
                "s3_content": line_s3,
                "l1_content": line_l1
            })
            
    is_equivalent = (len(differences) == 0)
    
    return {
        "status": "EQUIVALENT_TO_S3_REFERENCE" if is_equivalent else "DISCREPANCY_DETECTED",
        "governing_classification": "L1_BASELINE = REUSE_S3_REFERENCE",
        "is_equivalent": is_equivalent,
        "total_non_comment_lines_s3": len(s3_lines),
        "total_non_comment_lines_l1": len(l1_lines),
        "differences_count": len(differences),
        "differences": differences[:10],
        "submission_action": "OMIT_FROM_CLUSTER_SUBMISSIONS_REUSE_S3"
    }


def compute_initial_stiffness(u: np.ndarray, f: np.ndarray, u_max_linear: float = 0.0010) -> Tuple[float, float, float]:
    """
    Compute initial structural stiffness K0 via linear regression on initial elastic range.
    Returns (K0, intercept, R^2).
    """
    mask = (u > 0.0) & (u <= u_max_linear)
    if np.count_nonzero(mask) < 5:
        return (0.0, 0.0, 0.0)
    u_fit = u[mask]
    f_fit = f[mask]
    
    slope, intercept = np.polyfit(u_fit, f_fit, 1)
    f_pred = slope * u_fit + intercept
    ss_tot = np.sum((f_fit - np.mean(f_fit))**2)
    ss_res = np.sum((f_fit - f_pred)**2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return (float(slope), float(intercept), float(r2))


def resample_on_common_displacement(
    u_source: np.ndarray,
    vals_source: np.ndarray,
    u_target_grid: np.ndarray
) -> np.ndarray:
    """
    Resample trajectory onto target displacement grid with ZERO extrapolation.
    Values outside source range are set to NaN.
    """
    u_min = np.min(u_source)
    u_max = np.max(u_source)
    
    resampled = np.interp(u_target_grid, u_source, vals_source, left=np.nan, right=np.nan)
    return resampled


def evaluate_length_scale_sensitivity(
    trajectories: Dict[str, Dict[str, np.ndarray]],
    u_checkpoints: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform multi-quantity length-scale sensitivity analysis across provided candidates.
    """
    if u_checkpoints is None:
        u_checkpoints = [0.0010, 0.0020, 0.0030, 0.0040, 0.0050, 0.0055, 0.00585, 0.0060, 0.0070, 0.0080]
        
    results = {
        "study_type": "phase_field_length_scale_sensitivity_characterization",
        "governing_terminology": "phase_field_length_scale_sensitivity",
        "candidates": {},
        "pairwise_comparisons": {}
    }
    
    for cid, data in trajectories.items():
        u = data["u"]
        f = data["f"]
        e_elas = data.get("e_elas", np.zeros_like(u))
        e_frac = data.get("e_frac", np.zeros_like(u))
        w_ext = data.get("w_ext", np.zeros_like(u))
        
        k0, intercept, r2 = compute_initial_stiffness(u, f)
        idx_peak = int(np.argmax(f))
        f_max = float(f[idx_peak])
        u_peak = float(u[idx_peak])
        
        results["candidates"][cid] = {
            "candidate_id": cid,
            "k0_kn_per_mm": k0,
            "k0_r2": r2,
            "f_max_kn": f_max,
            "u_peak_mm": u_peak,
            "f_final_kn": float(f[-1]),
            "u_final_mm": float(u[-1]),
            "w_ext_final_mj": float(w_ext[-1] * 1000.0) if len(w_ext) > 0 else 0.0,
            "e_frac_final_mj": float(e_frac[-1] * 1000.0) if len(e_frac) > 0 else 0.0
        }
        
    return results


if __name__ == "__main__":
    print("=== Phase-Field Length-Scale Sensitivity Pipeline Audit ===")
    eq_result = verify_l1_s3_equivalence()
    print("L1 vs S3 Equivalence Status:", eq_result["status"])
    print("Classification:", eq_result.get("governing_classification"))
    print("Differences Count:", eq_result.get("differences_count"))
