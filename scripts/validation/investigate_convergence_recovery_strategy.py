#!/usr/bin/env python3
"""Investigate convergence-recovery strategy for Package 163 Stage C2-1.

Analyzes telemetry from Job 1419489.mmaster02 (Package 163-R2) and Job 1419490.mmaster02
(Package 157-R8), evaluates asymptotic contraction rates, projects coupled convergence
iteration targets, and compares intermediate hot-restart vs clean 300-outer contingency solve.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple


def calculate_contraction_rate(
    history: List[float], window: int = 20
) -> Tuple[float, float, float]:
    """Calculate geometric contraction rate rho over a trailing window.

    Returns (rho, val_start, val_end).
    """
    if len(history) < window or window < 2:
        return 1.0, 0.0, 0.0
    sub = history[-window:]
    val_start = sub[0]
    val_end = sub[-1]
    if val_start <= 0 or val_end <= 0:
        return 1.0, val_start, val_end
    rho = (val_end / val_start) ** (1.0 / (window - 1))
    return rho, val_start, val_end


def project_iterations_to_tolerance(
    current_val: float, target_tol: float, rho: float
) -> int:
    """Project outer iterations required to reach target_tol under contraction rate rho."""
    if current_val <= target_tol:
        return 0
    if rho >= 1.0 or rho <= 0.0:
        return 999999
    # target_tol = current_val * rho^n => n = ln(target_tol / current_val) / ln(rho)
    n = math.log(target_tol / current_val) / math.log(rho)
    return max(0, int(math.ceil(n)))


def analyze_convergence_recovery(
    p163_telemetry_path: Path,
    p157_telemetry_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    with open(p163_telemetry_path, "r", encoding="utf-8") as f:
        p163_data = json.load(f)

    with open(p157_telemetry_path, "r", encoding="utf-8") as f:
        p157_data = json.load(f)

    # Filter valid iterations with delta_u and delta_h
    u_vals = [r["delta_u"] for r in p163_data if r.get("delta_u") is not None]
    h_vals = [r["delta_h"] for r in p163_data if r.get("delta_h") is not None]
    d_vals = [r["delta_d"] for r in p163_data if r.get("delta_d") is not None]
    outer_vals = [r["outer"] for r in p163_data if r.get("delta_u") is not None]

    latest_outer = p163_data[-1]["outer"]
    latest_delta_d = p163_data[-1]["delta_d"]
    latest_delta_u = p163_data[-1].get("delta_u")
    latest_delta_h = p163_data[-1].get("delta_h")
    latest_pdas_active = p163_data[-1].get("pdas_active_count", 0)
    latest_dual_err = p163_data[-1].get("dual_error", 0.0)
    latest_free_err = p163_data[-1].get("free_error", 0.0)

    # Contraction rates over last 20 iterations
    rho_u, u_start, u_end = calculate_contraction_rate(u_vals, window=20)
    rho_h, h_start, h_end = calculate_contraction_rate(h_vals, window=20)

    # Tolerances defined by Stage C2-1 contract
    tol_u = 1.0e-9  # mm
    tol_h = 1.0e-4  # MPa
    tol_d = 1.0e-5  # dimensionless

    remaining_steps_u = project_iterations_to_tolerance(latest_delta_u, tol_u, rho_u)
    remaining_steps_h = project_iterations_to_tolerance(latest_delta_h, tol_h, rho_h)

    projected_converged_outer_u = latest_outer + remaining_steps_u
    projected_converged_outer_h = latest_outer + remaining_steps_h
    simultaneous_projected_outer = max(projected_converged_outer_u, projected_converged_outer_h)

    # Value at outer 200 budget limit
    remaining_to_200 = max(0, 200 - latest_outer)
    projected_u_at_200 = latest_delta_u * (rho_u ** remaining_to_200)
    projected_h_at_200 = latest_delta_h * (rho_h ** remaining_to_200)

    budget_exceeded_risk = simultaneous_projected_outer > 200

    # Resource assessment for contingency solve (max_outer = 300)
    sec_per_outer = 36.5  # empirical average on mnode097
    walltime_hours_300 = (300 * sec_per_outer) / 3600.0
    walltime_limit_hours = 8.0
    walltime_headroom_hours = walltime_limit_hours - walltime_hours_300

    # Assessment of recovery strategies
    strategy_comparison = {
        "strategy_1_intermediate_hot_restart": {
            "description": "Hot-start from unconverged subproblem intermediate directory (e.g. outer 180 or 200)",
            "driver_support": False,
            "technical_risks": [
                "Driver driver_package163_r2_c5_continuation.py lacks CLI argument for intermediate resume.",
                "Intermediate state lacks converged checkpoint certification and committed history manifest.",
                "Non-accumulating history evaluation from an unconverged iterate risks state corruption.",
                "Modifying driver code in-flight breaches code immutability protocols."
            ],
            "recommendation": "DISQUALIFIED_UNREVIEWED_CODE_MODIFICATION"
        },
        "strategy_2_clean_300_outer_contingency": {
            "description": "Clean contingency solve (Package 163-R3) initialized from authentic Checkpoint 01 with max_outer=300",
            "driver_support": True,
            "driver_flag": "--max-outer 300",
            "initial_state": "converged_checkpoint_01.json (Job 1419485.mmaster02, SHA-256 DCFD31186061FA81111DA18071CF8ADFB9BAF2C5CB343CB60F08416741C1B64A)",
            "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
            "estimated_walltime_hours": round(walltime_hours_300, 2),
            "walltime_ceiling_hours": walltime_limit_hours,
            "walltime_headroom_hours": round(walltime_headroom_hours, 2),
            "pbs_queue": "entry_imfdfkmq -> normal_imfdfkmq",
            "resource_conformance": "1 CPU, 16 GB RAM, <=8h (COMPLIANT)",
            "scientific_justification": [
                "Initializes from bitwise certified, physically accepted Checkpoint 01.",
                "Preserves exact non-accumulating history contract H*(x) = max(H0(x), psi_+(u*(x))).",
                "Requires zero driver source modifications (CLI parameter max_outer=300).",
                "Well within 8h PBS walltime limit (~3.04h estimated for 300 iterations).",
                "Full deterministic audit trail from Checkpoint 01 to Checkpoint 02."
            ],
            "recommendation": "QUALIFIED_PREFERRED_CONTINGENCY"
        }
    }

    # Analyze P157-R8 C4 reference progress
    p157_latest = p157_data[-1] if p157_data else {}
    p157_u = [r["delta_u"] for r in p157_data if r.get("delta_u") is not None]
    p157_status = {
        "count": len(p157_data),
        "latest_outer": p157_latest.get("outer"),
        "target_uy_mm": p157_latest.get("target_uy"),
        "delta_d": p157_latest.get("delta_d"),
        "delta_u_mm": p157_latest.get("delta_u"),
        "delta_h_MPa": p157_latest.get("delta_h"),
        "dual_error": p157_latest.get("dual_error"),
        "free_error": p157_latest.get("free_error"),
        "active_contraction": len(p157_u) > 1 and p157_u[-1] < p157_u[0]
    }

    result = {
        "schema": 1,
        "investigation_type": "CONVERGENCE_RECOVERY_STRATEGY_ASSESSMENT",
        "job_1419489_p163_r2": {
            "latest_outer": latest_outer,
            "latest_delta_d": latest_delta_d,
            "latest_delta_u_mm": latest_delta_u,
            "latest_delta_h_MPa": latest_delta_h,
            "latest_pdas_active_nodes": latest_pdas_active,
            "latest_kkt_dual_error": latest_dual_err,
            "latest_kkt_free_error": latest_free_err,
            "rho_u_20iter": round(rho_u, 5),
            "rho_h_20iter": round(rho_h, 5),
            "projected_converged_outer_u": projected_converged_outer_u,
            "projected_converged_outer_h": projected_converged_outer_h,
            "simultaneous_projected_outer": simultaneous_projected_outer,
            "projected_u_at_outer_200": projected_u_at_200,
            "projected_h_at_outer_200": projected_h_at_200,
            "budget_ceiling_outer": 200,
            "budget_exceeded_risk": budget_exceeded_risk,
            "status": "RUNNING_APPROACHING_BUDGET_CEILING"
        },
        "job_1419490_p157_r8": p157_status,
        "strategies": strategy_comparison,
        "recommended_action": (
            "Allow Job 1419489.mmaster02 to reach authentic terminal completion. "
            "If terminal status is NONCONVERGED (outer 200), immediately dispatch "
            "Package 163-R3 with max_outer=300 from authentic Checkpoint 01 under Strategy 2."
        )
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def main():
    p163_telemetry = Path("results/validation/p163_r2_live_iteration_telemetry.json")
    p157_telemetry = Path("results/validation/p157_r8_live_iteration_telemetry.json")
    output_path = Path("results/validation/convergence_recovery_investigation_turn32.json")

    res = analyze_convergence_recovery(p163_telemetry, p157_telemetry, output_path)
    print("Convergence Recovery Strategy Investigation Complete.")
    print(f"P163-R2 Outer: {res['job_1419489_p163_r2']['latest_outer']}")
    print(f"Contraction Rates: rho_u={res['job_1419489_p163_r2']['rho_u_20iter']}, rho_h={res['job_1419489_p163_r2']['rho_h_20iter']}")
    print(f"Projected Simultaneous Coupled Convergence: Outer {res['job_1419489_p163_r2']['simultaneous_projected_outer']}")
    print(f"Budget Exceeded Risk: {res['job_1419489_p163_r2']['budget_exceeded_risk']}")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
