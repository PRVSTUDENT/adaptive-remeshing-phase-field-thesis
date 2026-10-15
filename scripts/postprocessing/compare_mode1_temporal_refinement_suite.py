"""Mode-I Temporal Refinement and Minimum Increment Sensitivity Synthesis Framework.

Task: F1480-SUBMIT-PACKAGE44-SERIAL-PARITY-AND-VALIDATE-TEMPORAL-PHYSICS
Author: gemini-antigravity
Protocol: Version 2

Compares across 5 governed models:
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
    if "W_ext_mJ" in ref_dict and "W_ext_mJ" in candidate_dict:
        w_ref = ref_dict["W_ext_mJ"]
        w_cand = candidate_dict["W_ext_mJ"]
        metrics["delta_W_ext_pct"] = (w_cand - w_ref) / w_ref * 100.0

    return metrics


def evaluate_temporal_suite_manifest():
    """Produce the synthesis metadata manifest across the active temporal suite."""
    manifest = {
        "suite_name": "Mode-I Temporal Refinement and Sensitivity Suite",
        "governing_gate": "GATE_6B_TEMPORAL_CONVERGENCE_AND_PARITY",
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
            }
        }
    }
    return manifest

if __name__ == "__main__":
    m = evaluate_temporal_suite_manifest()
    print(json.dumps(m, indent=2))
