#!/usr/bin/env python3
"""
diagnose_package163_convergence.py
Detailed numerical diagnosis of Package 163 (Job 1419488) 100-iteration convergence trajectory.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
"""

import json
from pathlib import Path

def diagnose():
    telemetry_path = Path("results/validation/package163_live_iteration_telemetry.json")
    with open(telemetry_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    total_iters = len(records)
    rec_by_outer = {r["outer"]: r for r in records}

    milestones = [1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    milestone_summary = []
    for m in milestones:
        if m in rec_by_outer:
            r = rec_by_outer[m]
            milestone_summary.append({
                "outer": r["outer"],
                "delta_d": r["delta_d"],
                "delta_u": r["delta_u"],
                "delta_h": r["delta_h"],
                "dual_error": r["dual_error"],
                "free_error": r["free_error"],
                "pdas_active_count": r["pdas_active_count"],
                "kkt_active_count": r["kkt_active_count"]
            })

    # Last 30 iterations (70-100) statistics
    last_30 = [r for r in records if r["outer"] >= 70]
    delta_d_vals = [r["delta_d"] for r in last_30]
    delta_u_vals = [r["delta_u"] for r in last_30 if r["delta_u"] is not None]
    delta_h_vals = [r["delta_h"] for r in last_30 if r["delta_h"] is not None]
    pdas_act_vals = [r["pdas_active_count"] for r in last_30]
    kkt_act_vals = [r["kkt_active_count"] for r in last_30]

    # Check for limit cycle / oscillation
    # Let's inspect unique active set counts over iterations 80 to 100
    last_20 = [r for r in records if r["outer"] >= 80]
    pdas_pattern = [r["pdas_active_count"] for r in last_20]
    delta_d_pattern = [r["delta_d"] for r in last_20]

    diagnosis_result = {
        "schema": 1,
        "job_id": "1419488.mmaster02",
        "total_outer_iterations": total_iters,
        "milestones": milestone_summary,
        "last_30_stats": {
            "delta_d": {
                "min": min(delta_d_vals),
                "max": max(delta_d_vals),
                "mean": sum(delta_d_vals) / len(delta_d_vals),
                "final": delta_d_vals[-1],
                "target_tol": 1.0e-5,
                "converged": delta_d_vals[-1] <= 1.0e-5
            },
            "delta_u": {
                "min": min(delta_u_vals),
                "max": max(delta_u_vals),
                "mean": sum(delta_u_vals) / len(delta_u_vals),
                "final": delta_u_vals[-1],
                "target_tol": 1.0e-9,
                "converged": delta_u_vals[-1] <= 1.0e-9
            },
            "delta_h": {
                "min": min(delta_h_vals),
                "max": max(delta_h_vals),
                "mean": sum(delta_h_vals) / len(delta_h_vals),
                "final": delta_h_vals[-1],
                "target_tol": 1.0e-4,
                "converged": delta_h_vals[-1] <= 1.0e-4
            },
            "pdas_active_count": {
                "min": min(pdas_act_vals),
                "max": max(pdas_act_vals),
                "unique_values": sorted(list(set(pdas_act_vals))),
                "final": pdas_act_vals[-1]
            },
            "kkt_active_count": {
                "min": min(kkt_act_vals),
                "max": max(kkt_act_vals),
                "unique_values": sorted(list(set(kkt_act_vals))),
                "final": kkt_act_vals[-1]
            }
        },
        "kkt_residuals_final": {
            "dual_error": records[-1]["dual_error"],
            "free_error": records[-1]["free_error"],
            "target_tol": 1.0e-6,
            "dual_converged": records[-1]["dual_error"] <= 1.0e-6,
            "free_converged": records[-1]["free_error"] <= 1.0e-6
        },
        "oscillation_signature": {
            "last_20_pdas_counts": pdas_pattern,
            "last_10_delta_d": [f"{v:.4e}" for v in delta_d_pattern[-10:]],
            "is_plateau_or_cycle": max(pdas_act_vals) - min(pdas_act_vals) <= 2
        }
    }

    out_path = Path("results/validation/package163_convergence_diagnosis.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(diagnosis_result, f, indent=2)

if __name__ == "__main__":
    diagnose()
