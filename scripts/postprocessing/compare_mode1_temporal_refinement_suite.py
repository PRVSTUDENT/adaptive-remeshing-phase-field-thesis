"""Mode-I Temporal Refinement, Minimum Increment Sensitivity, and Coarse Mesh Resolution Suite.

Tasks: F1480 / F1481
Authors: gemini-antigravity
Protocol: Version 2
Governance Gate: GATE_6B_ACTIVE_EVALUATION_AND_CONTINUATION

Models Evaluated:
1. Canonical Fixed-Mesh 15k Reference Anchor (Job 1398090, 15,192 FE):
   - F_max = 0.757778 kN, u_peak = 0.005857 mm, K_0 = 137.945520 kN/mm
   - W_ext = 2.3587 mJ (canonical reference work across full [0.0, 0.0100] mm horizon)
2. Package 40 Baseline (Jobs 1412465, 1412873, 1413022, 14,483 FE, dt_max=2E-4, dt_min=1E-9):
   - F_max = 0.743701 kN, u_peak = 0.005733 mm, K_0 = 137.9096 kN/mm
   - Attained horizon: u = 0.007889 mm (Exit 1 due to dt < dt_min cutback exhaustion)
   - W_ext = 2.2674 mJ (-3.87% vs canonical 15k reference)
   - Softening: 99.76% softened (RF_final = 1.76 N)
3. Package 43 Minimum Increment Sensitivity (Job 1413217, 14,483 FE, dt_min=1E-15, 8T SMP):
   - Evaluates whether relaxing dt_min allows traversing steep post-severance transition
4. Package 44 Controlled Temporal Refinement (Job 1413278, 14,483 FE, dt_max=1E-4, 8T SMP):
   - Evaluates temporal discretization sensitivity with du = 0.5 nm (nominal 10,000 increments)
5. Package 45 Serial Parity Control (Job 1413296, 14,483 FE, dt_max=1E-4, 1-CPU serial):
   - Certifies Stage-A serial/thread parity against multi-threading race conditions
6. Package 46 Coarse Pre-Analysis Resolution Sensitivity (PK_M1_COARSE_FINE_CONT, 4,900 CPE4):
   - Evaluates effect of preliminary coarse mesh density (h=14.3 um vs 33 um) on MISESERI localization
"""

import json
import math
import os
import sys

# Reference Baseline Values
FIXED_MESH_REFERENCE = {
    "job_id": "1398090.mmaster02",
    "name": "Canonical Fixed-Mesh 15k Reference",
    "elements": 15192,
    "nodes": 15456,
    "cpus": 1,
    "mode": "serial",
    "K_0_kN_per_mm": 137.945520,
    "F_max_kN": 0.757778,
    "u_peak_mm": 0.005857,
    "W_ext_mJ": 2.3587,
    "W_ext_full_mJ": 2.3587,
    "attained_u_mm": 0.0100,
    "exit_status": 0
}

PACKAGE_40_BASELINE = {
    "job_ids": ["1412465.mmaster02", "1412873.mmaster02", "1413022.mmaster02"],
    "name": "Package 40 Corrected Method B Baseline (dt_max=2E-4, dt_min=1E-9)",
    "elements": 14483,
    "nodes": 14757,
    "K_0_kN_per_mm": 137.9096,
    "F_max_kN": 0.743701,
    "u_peak_mm": 0.005733,
    "W_ext_mJ": 2.2674,
    "attained_u_mm": 0.007889,
    "exit_status": 1,
    "termination_reason": "CUTBACK_EXHAUSTION_AT_DTMIN_1E9"
}

PACKAGE_90_COARSE_BASELINE = {
    "job_id": "1409914.mmaster02",
    "name": "Package 90 Continuum Control Baseline (2,906 elements)",
    "elements": 2906,
    "nodes": 2988,
    "nominal_h_mm": 0.033,
    "crack_tip_coord": [0.5, 0.5],
    "miseseri_peak_MPa": 0.950009,
    "miseseri_mean_MPa": 0.009878,
    "misesavg_MPa": 35.459,
    "far_field_error_share_pct": 65.57,
    "crack_tip_error_share_pct": 22.13,
    "ligament_error_share_pct": 12.30
}

# Predeclared Matched Evaluation Points
MATCHED_EVALUATION_POINTS = [
    {"point_id": "P1_LINEAR_LIMIT", "u_mm": 0.005000, "description": "End of Step 1 linear elastic regime"},
    {"point_id": "P2_PKG40_PEAK", "u_mm": 0.005733, "description": "Package 40 baseline peak load state"},
    {"point_id": "P3_REF15K_PEAK", "u_mm": 0.005857, "description": "Canonical 15k reference peak load state"},
    {"point_id": "P4_POST_PEAK_EARLY", "u_mm": 0.006000, "description": "Early softening post-peak transition"},
    {"point_id": "P5_PKG40_HORIZON", "u_mm": 0.007889, "description": "Package 40 baseline severance termination limit"}
]


def compute_parity_metrics(ref_dict, candidate_dict):
    """Compute relative differences for multi-quantity parity evaluation."""
    metrics = {}
    
    # K0 difference
    if "K_0_kN_per_mm" in ref_dict and "K_0_kN_per_mm" in candidate_dict:
        k0_ref = ref_dict["K_0_kN_per_mm"]
        k0_cand = candidate_dict["K_0_kN_per_mm"]
        metrics["delta_K0_pct"] = (k0_cand - k0_ref) / k0_ref * 100.0

    # Fmax difference
    if "F_max_kN" in ref_dict and "F_max_kN" in candidate_dict:
        fmax_ref = ref_dict["F_max_kN"]
        fmax_cand = candidate_dict["F_max_kN"]
        metrics["delta_Fmax_pct"] = (fmax_cand - fmax_ref) / fmax_ref * 100.0

    # u_peak difference
    if "u_peak_mm" in ref_dict and "u_peak_mm" in candidate_dict:
        u_ref = ref_dict["u_peak_mm"]
        u_cand = candidate_dict["u_peak_mm"]
        metrics["delta_u_peak_pct"] = (u_cand - u_ref) / u_ref * 100.0

    # W_ext difference
    w_ref = ref_dict.get("W_ext_mJ") or ref_dict.get("W_ext_full_mJ")
    w_cand = candidate_dict.get("W_ext_mJ") or candidate_dict.get("W_ext_full_mJ")
    if w_ref is not None and w_cand is not None:
        metrics["delta_W_ext_pct"] = (w_cand - w_ref) / w_ref * 100.0

    return metrics


def evaluate_coarse_resolution_scaling(h_baseline, h_candidate, p_rate=2.0):
    """
    Theoretical discretization error scaling for smooth far-field linear elasticity.
    e_far ~ O(h^p), singular tip error e_tip ~ O(h^(p/2) or diverges in point stress).
    """
    ratio_h = h_candidate / h_baseline
    predicted_far_field_ratio = math.pow(ratio_h, p_rate)
    return {
        "h_ratio": ratio_h,
        "predicted_far_field_error_ratio": predicted_far_field_ratio,
        "theoretical_scaling": f"Far-field error scales as O(h^{p_rate}), reducing far-field noise by factor {1.0/predicted_far_field_ratio:.2f}x"
    }


def evaluate_temporal_suite_manifest():
    """Produce the synthesis metadata manifest across the active temporal and spatial suite."""
    manifest = {
        "suite_name": "Mode-I Temporal Refinement, Minimum Increment, and Coarse Resolution Suite",
        "governing_gate": "GATE_6B_ACTIVE_EVALUATION_AND_CONTINUATION",
        "matched_evaluation_points": MATCHED_EVALUATION_POINTS,
        "cases": {
            "canonical_reference": FIXED_MESH_REFERENCE,
            "package_40_baseline": PACKAGE_40_BASELINE,
            "package_43_dtmin_sensitivity": {
                "job_id": "1413217.mmaster02",
                "name": "M1_MB_DTMIN_8T",
                "parameters": {"dt_min": 1.0e-15, "dt_max": 2.0e-4, "cpus": 8, "mode": "threads"}
            },
            "package_44_dtmax_temporal_refinement": {
                "job_id": "1413278.mmaster02",
                "name": "M1_MB_DTMAX_8T",
                "parameters": {"dt_min": 1.0e-9, "dt_max": 1.0e-4, "cpus": 8, "mode": "threads", "inc_max": 12000}
            },
            "package_45_serial_parity_control": {
                "job_id": "1413296.mmaster02",
                "name": "M1_MB_DTMAX_1C",
                "parameters": {"dt_min": 1.0e-9, "dt_max": 1.0e-4, "cpus": 1, "mode": "serial", "inc_max": 12000}
            },
            "package_46_coarse_preanalysis_resolution": {
                "job_id": "PENDING_OR_LOCAL",
                "name": "PK_M1_COARSE_FINE_CONT",
                "parameters": {"elements": 4900, "nominal_h_mm": 0.0142857, "cpus": 1, "mode": "serial"}
            }
        }
    }
    return manifest


if __name__ == "__main__":
    m = evaluate_temporal_suite_manifest()
    print(json.dumps(m, indent=2))
