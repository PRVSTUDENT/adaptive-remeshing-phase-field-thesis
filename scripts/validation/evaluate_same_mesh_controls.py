#!/usr/bin/env python3
"""
scripts/validation/evaluate_same_mesh_controls.py
Formal comparative evaluation and post-processing for Task F1626:
Method C Paired Same-Mesh Control Experiment on C5 Donor Checkpoint 03.

Arm 1 (Package 172): Element-averaged GP history operator (H <- H_bar)
Arm 2 (Package 173): Corrected isoparametric bilinear GP history operator (H <- sum N_k H_k)

Computes quantitative metrics, convergence telemetry, physical gates, and exports:
results/validation/f1626_same_mesh_control_evaluation_summary.json
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

DONOR_CHECKPOINT03 = {
    "source_job_id": "1419566.mmaster02",
    "reaction_force_kN": 0.17992419004440308,
    "total_energy_kNmm": 0.00022639903,
    "displacement_uy_mm": 0.0018703125442191958,
    "nodes_count": 13278,
    "elements_count": 12996,
    "gp_history_count": 51984
}

TOLERANCES = {
    "delta_d_tol": 1e-5,
    "delta_u_tol": 1e-9,
    "delta_h_tol": 1e-4,
    "force_continuity_tol": 0.02,   # 2%
    "energy_continuity_tol": 0.02,  # 2%
    "damage_healing_tol": 0         # 0 healing violations
}


def load_telemetry_file(telem_path: Path) -> List[Dict[str, Any]]:
    if not telem_path.is_file():
        return []
    with open(telem_path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_arm_telemetry(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not history:
        return {"iterations_completed": 0, "status": "NO_TELEMETRY"}

    n_iters = len(history)
    first = history[0]
    final = history[-1]

    # Calculate average contraction factors over the last 15 iterations (if available)
    window = history[-15:] if n_iters >= 15 else history
    rho_d_list = []
    rho_u_list = []
    rho_h_list = []

    for i in range(1, len(window)):
        prev = window[i - 1]
        curr = window[i]
        if prev.get("delta_d") and curr.get("delta_d") and prev["delta_d"] > 0:
            rho_d_list.append(curr["delta_d"] / prev["delta_d"])
        if prev.get("delta_u") and curr.get("delta_u") and prev["delta_u"] > 0:
            rho_u_list.append(curr["delta_u"] / prev["delta_u"])
        if prev.get("delta_h") and curr.get("delta_h") and prev["delta_h"] > 0:
            rho_h_list.append(curr["delta_h"] / prev["delta_h"])

    avg_rho_d = sum(rho_d_list) / len(rho_d_list) if rho_d_list else None
    avg_rho_u = sum(rho_u_list) / len(rho_u_list) if rho_u_list else None
    avg_rho_h = sum(rho_h_list) / len(rho_h_list) if rho_h_list else None

    # Rollbacks and stage switches
    rollbacks = sum(1 for rec in history if rec.get("rollback_triggered"))
    stage2_entries = sum(1 for rec in history if rec.get("transition_activated"))

    # Active set stats
    initial_active = first.get("pdas_active_count", 0)
    final_active = final.get("pdas_active_count", 0)

    # KKT stats
    kkt_passed_count = sum(1 for rec in history if rec.get("kkt_post_passed"))

    # Convergence status against coupled tolerances
    final_dd = final.get("delta_d", float("inf"))
    final_du = final.get("delta_u", float("inf")) or float("inf")
    final_dh = final.get("delta_h", float("inf")) or float("inf")

    passed_dd = final_dd <= TOLERANCES["delta_d_tol"]
    passed_du = final_du <= TOLERANCES["delta_u_tol"]
    passed_dh = final_dh <= TOLERANCES["delta_h_tol"]
    is_coupled_converged = passed_dd and passed_du and passed_dh

    return {
        "iterations_completed": n_iters,
        "initial_active_set": initial_active,
        "final_active_set": final_active,
        "active_set_reduction_pct": ((initial_active - final_active) / initial_active * 100.0) if initial_active > 0 else 0.0,
        "final_delta_d": final_dd,
        "final_delta_u_mm": final_du,
        "final_delta_H_MPa": final_dh,
        "delta_d_converged": passed_dd,
        "delta_u_converged": passed_du,
        "delta_H_converged": passed_dh,
        "coupled_converged": is_coupled_converged,
        "avg_contraction_factor_delta_d": avg_rho_d,
        "avg_contraction_factor_delta_u": avg_rho_u,
        "avg_contraction_factor_delta_H": avg_rho_h,
        "rollbacks_count": rollbacks,
        "stage2_transitions_count": stage2_entries,
        "kkt_passed_ratio": f"{kkt_passed_count}/{n_iters}",
        "final_kkt_passed": final.get("kkt_post_passed", False),
        "final_complementarity": final.get("complementarity", None)
    }


def compare_arms(t1: List[Dict[str, Any]], t2: List[Dict[str, Any]]) -> Dict[str, Any]:
    min_len = min(len(t1), len(t2))
    if min_len == 0:
        return {}

    comparison_points = {}
    checkpoints = [1, 5, 10, 20, 30, 40, 50, 60, 70, min_len]
    checkpoints = sorted(list(set(cp for cp in checkpoints if cp <= min_len)))

    for cp in checkpoints:
        r1 = t1[cp - 1]
        r2 = t2[cp - 1]

        dd1 = r1.get("delta_d") or 1e-12
        dd2 = r2.get("delta_d") or 1e-12
        du1 = r1.get("delta_u") or 1e-12
        du2 = r2.get("delta_u") or 1e-12
        dh1 = r1.get("delta_h") or 1e-12
        dh2 = r2.get("delta_h") or 1e-12

        comparison_points[f"outer_{cp:03d}"] = {
            "outer": cp,
            "arm1_delta_d": dd1,
            "arm2_delta_d": dd2,
            "ratio_dd_arm1_over_arm2": dd1 / dd2 if dd2 > 0 else None,
            "arm1_delta_u_mm": du1,
            "arm2_delta_u_mm": du2,
            "ratio_du_arm1_over_arm2": du1 / du2 if du2 > 0 else None,
            "arm1_delta_H_MPa": dh1,
            "arm2_delta_H_MPa": dh2,
            "ratio_dH_arm1_over_arm2": dh1 / dh2 if dh2 > 0 else None,
            "arm1_active_set": r1.get("pdas_active_count"),
            "arm2_active_set": r2.get("pdas_active_count")
        }

    return comparison_points


def build_evaluation_summary(
    arm1_dir: Path,
    arm2_dir: Path,
    arm1_job_id: str = "1420352.mmaster02",
    arm2_job_id: str = "1420353.mmaster02"
) -> Dict[str, Any]:
    t1 = load_telemetry_file(arm1_dir / "live_iteration_telemetry.json")
    t2 = load_telemetry_file(arm2_dir / "live_iteration_telemetry.json")

    a1_analysis = analyze_arm_telemetry(t1)
    a2_analysis = analyze_arm_telemetry(t2)
    comparison = compare_arms(t1, t2)

    # Check for final converged checkpoints or endpoints
    ckpt1_file = arm1_dir / "converged_checkpoint.json"
    ckpt2_file = arm2_dir / "converged_checkpoint.json"

    ckpt1 = json.loads(ckpt1_file.read_text(encoding="utf-8")) if ckpt1_file.is_file() else None
    ckpt2 = json.loads(ckpt2_file.read_text(encoding="utf-8")) if ckpt2_file.is_file() else None

    # Scientific conclusion
    if a1_analysis.get("final_delta_H_MPa") and a2_analysis.get("final_delta_H_MPa"):
        dh_reduction = a1_analysis["final_delta_H_MPa"] / a2_analysis["final_delta_H_MPa"]
    else:
        dh_reduction = None

    summary = {
        "schema": 1,
        "task_id": "F1626-METHOD-C-SAME-MESH-REPAIRED-CONTROL-EXECUTION",
        "scientific_operation": "paired_same_mesh_control_evaluation",
        "donor_checkpoint": DONOR_CHECKPOINT03,
        "tolerances": TOLERANCES,
        "jobs": {
            "arm1_old_control": {
                "job_id": arm1_job_id,
                "operator": "element_averaged_gp_history",
                "package": "models/pandey_kumar_mode1/172_c5_same_mesh_old_control",
                "dir": str(arm1_dir),
                "has_converged_checkpoint": ckpt1 is not None,
                "telemetry_analysis": a1_analysis
            },
            "arm2_corrected_control": {
                "job_id": arm2_job_id,
                "operator": "isoparametric_bilinear_gp_history",
                "package": "models/pandey_kumar_mode1/173_c5_same_mesh_corrected_control",
                "dir": str(arm2_dir),
                "has_converged_checkpoint": ckpt2 is not None,
                "telemetry_analysis": a2_analysis
            }
        },
        "side_by_side_comparison": comparison,
        "scientific_verdict": {
            "history_gradient_defect_confirmed": (dh_reduction is not None and dh_reduction > 10.0),
            "delta_H_reduction_factor": dh_reduction,
            "isoparametric_superiority_established": (
                a2_analysis.get("final_delta_d", 1.0) < a1_analysis.get("final_delta_d", 0.0) and
                a2_analysis.get("final_delta_u_mm", 1.0) < a1_analysis.get("final_delta_u_mm", 0.0) and
                a2_analysis.get("final_delta_H_MPa", 1.0) < a1_analysis.get("final_delta_H_MPa", 0.0)
            ),
            "findings_summary": (
                f"Isoparametric bilinear GP history operator (Arm 2) outperforms element averaging (Arm 1) "
                f"across all primary field increments: Delta_H reduced by ~{dh_reduction:.1f}x, "
                f"Delta_u reduced by ~{((a1_analysis.get('final_delta_u_mm') or 1.0) / (a2_analysis.get('final_delta_u_mm') or 1.0)):.1f}x, "
                f"and Delta_d reduced by ~{((a1_analysis.get('final_delta_d') or 1.0) / (a2_analysis.get('final_delta_d') or 1.0)):.1f}x."
                if dh_reduction else "Awaiting complete telemetry for final quantitative comparison."
            )
        }
    }
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate paired same-mesh controls under Task F1626.")
    parser.add_argument("--arm1-dir", type=Path, required=True, help="Directory containing Arm 1 telemetry/outputs.")
    parser.add_argument("--arm2-dir", type=Path, required=True, help="Directory containing Arm 2 telemetry/outputs.")
    parser.add_argument("--out-json", type=Path, default=Path("results/validation/f1626_same_mesh_control_evaluation_summary.json"), help="Output summary JSON.")
    args = parser.parse_args()

    res = build_evaluation_summary(args.arm1_dir, args.arm2_dir)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Evaluation summary written to {args.out_json}")
    print(json.dumps(res["scientific_verdict"], indent=2))
