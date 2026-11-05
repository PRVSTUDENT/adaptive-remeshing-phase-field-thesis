#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/validation/evaluate_f1629_paired_execution.py
======================================================
Formal comparative evaluation and post-processing for Task F1629:
Method C Paired C6 R12 Controlled Overnight Production Execution.

Arm A (Package 174): Picard Baseline (anderson_enabled=False) on nonmatching C6 receiver
Arm B (Package 175): Safeguarded Anderson Acceleration (m=2, beta=0.85) on identical C6 receiver

Quantifies:
1. Contraction rates (rho_d, rho_u, rho_H) across iterations.
2. Anderson acceleration effectiveness: steps taken, damping, fallback, safeguards.
3. Physical continuity vs donor Checkpoint 03 (Job 1419566.mmaster02):
   - Held displacement: uy = 0.0018703125442191958 mm
   - Reaction force drift: |Fy - 0.179924| / 0.179924 <= 2%
   - Total energy drift: |E_tot - 0.0002264| / 0.0002264 <= 2%
4. Coupled tolerance satisfaction:
   - Delta d <= 1e-5
   - Delta u <= 1e-9 mm
   - Delta H <= 1e-4 MPa
5. Irreversibility: zero healing violations, d in [0, 1].

Outputs:
- results/validation/f1629_paired_execution_summary.json
- results/validation/f1629_paired_execution_report.md
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

DONOR_CHECKPOINT03 = {
    "source_job_id": "1419566.mmaster02",
    "reaction_force_kN": 0.17992419004440308,
    "total_energy_kNmm": 0.00022639903,
    "displacement_uy_mm": 0.0018703125442191958,
    "nodes_count": 13278,
    "elements_count": 12996,
    "gp_history_count": 51984,
}

RECEIVER_C6_TOPOLOGY = {
    "mesh_level": "C6",
    "elements_count": 15252,
    "nodes_count": 15559,
    "crack_seam_pairs": 59,
    "gp_history_count": 61008,
}

GATES = {
    "delta_d_tol": 1e-5,
    "delta_u_tol": 1e-9,
    "delta_h_tol": 1e-4,
    "kkt_tol": 1e-6,
    "force_continuity_tol": 0.02,   # 2%
    "energy_continuity_tol": 0.02,  # 2%
    "damage_healing_tol": 0,        # 0 healing violations
}


def load_telemetry(telem_file: Path) -> List[Dict[str, Any]]:
    """Loads iteration telemetry from a JSON file."""
    if not telem_file.is_file():
        return []
    with open(telem_file, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_endpoint_or_checkpoint(eq_dir: Path) -> Optional[Dict[str, Any]]:
    """Loads final checkpoint or evaluation summary from run directory."""
    if not eq_dir or not eq_dir.is_dir():
        return None
    for name in ["converged_checkpoint.json", "evaluation_summary.json", "endpoint.json"]:
        p = eq_dir / name
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception:
                pass
    return None


def calculate_contraction_factors(history: List[Dict[str, Any]], window_size: int = 15) -> Dict[str, Optional[float]]:
    """Calculates geometric mean of contraction factors over the last window."""
    if len(history) < 2:
        return {"avg_rho_d": None, "avg_rho_u": None, "avg_rho_h": None}

    window = history[-window_size:] if len(history) >= window_size else history
    rho_d, rho_u, rho_h = [], [], []

    for i in range(1, len(window)):
        prev = window[i - 1]
        curr = window[i]

        p_d = prev.get("delta_d") or prev.get("max_delta_d")
        c_d = curr.get("delta_d") or curr.get("max_delta_d")
        if p_d and c_d and p_d > 0 and c_d > 0:
            rho_d.append(c_d / p_d)

        p_u = prev.get("delta_u") or prev.get("max_delta_u")
        c_u = curr.get("delta_u") or curr.get("max_delta_u")
        if p_u and c_u and p_u > 0 and c_u > 0:
            rho_u.append(c_u / p_u)

        p_h = prev.get("delta_history") or prev.get("delta_h")
        c_h = curr.get("delta_history") or curr.get("delta_h")
        if p_h and c_h and p_h > 0 and c_h > 0:
            rho_h.append(c_h / p_h)

    def mean_or_none(vals: List[float]) -> Optional[float]:
        return sum(vals) / len(vals) if vals else None

    return {
        "avg_rho_d": mean_or_none(rho_d),
        "avg_rho_u": mean_or_none(rho_u),
        "avg_rho_h": mean_or_none(rho_h),
    }


def analyze_arm(name: str, package_name: str, pbs_job_id: str, history: List[Dict[str, Any]], final_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyzes one arm's complete telemetry."""
    if not history:
        return {
            "name": name,
            "package": package_name,
            "pbs_job_id": pbs_job_id,
            "iterations_completed": 0,
            "status": "NO_TELEMETRY",
        }

    n_iters = len(history)
    first = history[0]
    final = history[-1]

    contractions = calculate_contraction_factors(history)

    # Active set stats
    init_active = first.get("pdas_active_count", 0)
    final_active = final.get("pdas_active_count", 0)
    reduction_pct = ((init_active - final_active) / init_active * 100.0) if init_active > 0 else 0.0

    # Rollbacks and transitions
    rollbacks = sum(1 for r in history if r.get("rollback_triggered"))
    stage2_active = sum(1 for r in history if r.get("stage") == 2 or r.get("transition_activated"))

    # Anderson specific metrics (if present)
    anderson_steps = sum(1 for r in history if r.get("anderson_applied"))
    anderson_fallbacks = sum(1 for r in history if r.get("anderson_fallback"))

    # Final field increments
    final_dd = final.get("delta_d") if final.get("delta_d") is not None else final.get("max_delta_d", float("inf"))
    final_du = final.get("delta_u") if final.get("delta_u") is not None else final.get("max_delta_u", float("inf"))
    final_dh = final.get("delta_history") if final.get("delta_history") is not None else final.get("delta_h", float("inf"))

    # Physical continuity (if endpoint available)
    rf2 = None
    tot_e = None
    rf_drift = None
    e_drift = None
    healing_violations = None

    if final_state:
        rf2 = final_state.get("reaction_force_kN") or final_state.get("rf2_kN") or final_state.get("rf2")
        tot_e = final_state.get("total_energy_kNmm") or final_state.get("total_energy")
        healing_violations = final_state.get("healing_violations", 0)

        ref_rf = DONOR_CHECKPOINT03["reaction_force_kN"]
        ref_e = DONOR_CHECKPOINT03["total_energy_kNmm"]

        if rf2 is not None:
            rf_drift = abs(rf2 - ref_rf) / ref_rf
        if tot_e is not None:
            e_drift = abs(tot_e - ref_e) / ref_e

    # Gate evaluations
    gate_dd = final_dd <= GATES["delta_d_tol"]
    gate_du = final_du <= GATES["delta_u_tol"]
    gate_dh = final_dh <= GATES["delta_h_tol"]
    gate_coupled = gate_dd and gate_du and gate_dh
    gate_rf = (rf_drift is not None) and (rf_drift <= GATES["force_continuity_tol"])
    gate_energy = (e_drift is not None) and (e_drift <= GATES["energy_continuity_tol"])
    gate_healing = (healing_violations is not None) and (healing_violations <= GATES["damage_healing_tol"])

    all_accepted = gate_coupled and gate_rf and gate_energy and gate_healing

    return {
        "name": name,
        "package": package_name,
        "pbs_job_id": pbs_job_id,
        "iterations_completed": n_iters,
        "initial_active_set": init_active,
        "final_active_set": final_active,
        "active_set_reduction_pct": reduction_pct,
        "stage2_iterations": stage2_active,
        "rollback_events": rollbacks,
        "anderson_steps_applied": anderson_steps,
        "anderson_fallbacks": anderson_fallbacks,
        "final_delta_d": final_dd,
        "final_delta_u_mm": final_du,
        "final_delta_h_mpa": final_dh,
        "avg_rho_d_tail": contractions["avg_rho_d"],
        "avg_rho_u_tail": contractions["avg_rho_u"],
        "avg_rho_h_tail": contractions["avg_rho_h"],
        "reaction_force_kN": rf2,
        "total_energy_kNmm": tot_e,
        "reaction_force_drift": rf_drift,
        "total_energy_drift": e_drift,
        "damage_healing_violations": healing_violations,
        "gates": {
            "delta_d_pass": gate_dd,
            "delta_u_pass": gate_du,
            "delta_h_pass": gate_dh,
            "coupled_convergence_pass": gate_coupled,
            "reaction_force_continuity_pass": gate_rf,
            "total_energy_continuity_pass": gate_energy,
            "damage_healing_pass": gate_healing,
            "overall_physical_acceptance_pass": all_accepted,
        },
    }


def compare_arms(arm_a: Dict[str, Any], arm_b: Dict[str, Any]) -> Dict[str, Any]:
    """Compares Arm A (Picard) vs Arm B (Anderson M2)."""
    if arm_a.get("status") == "NO_TELEMETRY" or arm_b.get("status") == "NO_TELEMETRY":
        return {"comparison_valid": False, "reason": "Missing telemetry on at least one arm"}

    dd_a = arm_a["final_delta_d"]
    dd_b = arm_b["final_delta_d"]
    du_a = arm_a["final_delta_u_mm"]
    du_b = arm_b["final_delta_u_mm"]
    dh_a = arm_a["final_delta_h_mpa"]
    dh_b = arm_b["final_delta_h_mpa"]

    ratio_dd = (dd_a / dd_b) if (dd_b > 0 and not math.isinf(dd_b)) else None
    ratio_du = (du_a / du_b) if (du_b > 0 and not math.isinf(du_b)) else None
    ratio_dh = (dh_a / dh_b) if (dh_b > 0 and not math.isinf(dh_b)) else None

    # Iteration efficiency: if one converged earlier
    iter_a = arm_a["iterations_completed"]
    iter_b = arm_b["iterations_completed"]

    return {
        "comparison_valid": True,
        "anderson_over_picard_ratio_delta_d": ratio_dd,
        "anderson_over_picard_ratio_delta_u": ratio_du,
        "anderson_over_picard_ratio_delta_h": ratio_dh,
        "iterations_arm_a_picard": iter_a,
        "iterations_arm_b_anderson": iter_b,
        "anderson_active_reduction_gain_pct": arm_b["active_set_reduction_pct"] - arm_a["active_set_reduction_pct"],
        "both_arms_coupled_converged": arm_a["gates"]["coupled_convergence_pass"] and arm_b["gates"]["coupled_convergence_pass"],
        "arm_b_accelerated_convergence": arm_b["gates"]["coupled_convergence_pass"] and not arm_a["gates"]["coupled_convergence_pass"],
    }


def generate_markdown_report(summary: Dict[str, Any]) -> str:
    """Generates formal Markdown report for F1629."""
    a = summary["arm_a_picard"]
    b = summary["arm_b_anderson"]
    cmp = summary["comparison"]

    ratio_dd_txt = f"{cmp['anderson_over_picard_ratio_delta_d']:.2f}x reduction" if cmp.get("anderson_over_picard_ratio_delta_d") else "N/A"
    ratio_du_txt = f"{cmp['anderson_over_picard_ratio_delta_u']:.2f}x reduction" if cmp.get("anderson_over_picard_ratio_delta_u") else "N/A"
    ratio_dh_txt = f"{cmp['anderson_over_picard_ratio_delta_h']:.2f}x reduction" if cmp.get("anderson_over_picard_ratio_delta_h") else "N/A"

    rf_drift_a_txt = f"{a['reaction_force_drift']*100:.3f}%" if a.get("reaction_force_drift") is not None else "N/A"
    rf_drift_b_txt = f"{b['reaction_force_drift']*100:.3f}%" if b.get("reaction_force_drift") is not None else "N/A"

    e_drift_a_txt = f"{a['total_energy_drift']*100:.3f}%" if a.get("total_energy_drift") is not None else "N/A"
    e_drift_b_txt = f"{b['total_energy_drift']*100:.3f}%" if b.get("total_energy_drift") is not None else "N/A"

    lines = [
        "# Method C Paired C6 R12 Controlled Production Execution Report",
        "",
        f"**Task ID:** `{summary['task_id']}`  ",
        f"**Date:** {summary['timestamp']}  ",
        f"**Donor Reference:** Checkpoint 03 (Job `{DONOR_CHECKPOINT03['source_job_id']}`, $u_y = {DONOR_CHECKPOINT03['displacement_uy_mm']}$ mm)  ",
        f"**Receiver Mesh:** C6 Nonmatching Adaptive Mesh ({RECEIVER_C6_TOPOLOGY['elements_count']} CPE4 quads, {RECEIVER_C6_TOPOLOGY['nodes_count']} nodes, {RECEIVER_C6_TOPOLOGY['crack_seam_pairs']} seam pairs)  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "This experiment isolates the effect of **safeguarded limited-memory Anderson acceleration ($m=2, \\beta=0.85$)** on coupled staggered PDAS re-equilibration following gradient-preserving isoparametric bilinear Gauss-point state transfer onto the nonmatching C6 adaptive receiver mesh.",
        "",
        "| Quantity | Arm A: Picard Baseline (P174) | Arm B: Safeguarded Anderson M2 (P175) | Comparative Ratio / Gain |",
        "| :--- | :---: | :---: | :---: |",
        f"| **PBS Job ID** | `{a.get('pbs_job_id', 'N/A')}` | `{b.get('pbs_job_id', 'N/A')}` | - |",
        f"| **Iterations Completed** | {a.get('iterations_completed', 0)} | {b.get('iterations_completed', 0)} | - |",
        f"| **Final $\\Delta d$** | `{a.get('final_delta_d', 'N/A'):.4e}` | `{b.get('final_delta_d', 'N/A'):.4e}` | {ratio_dd_txt} |",
        f"| **Final $\\Delta u$ [mm]** | `{a.get('final_delta_u_mm', 'N/A'):.4e}` | `{b.get('final_delta_u_mm', 'N/A'):.4e}` | {ratio_du_txt} |",
        f"| **Final $\\Delta H$ [MPa]** | `{a.get('final_delta_h_mpa', 'N/A'):.4e}` | `{b.get('final_delta_h_mpa', 'N/A'):.4e}` | {ratio_dh_txt} |",
        f"| **Active Set Contraction** | {a.get('initial_active_set', 0)} -> {a.get('final_active_set', 0)} ({a.get('active_set_reduction_pct', 0.0):.1f}%) | {b.get('initial_active_set', 0)} -> {b.get('final_active_set', 0)} ({b.get('active_set_reduction_pct', 0.0):.1f}%) | {cmp.get('anderson_active_reduction_gain_pct', 0.0):+.1f}% |",
        f"| **Coupled Convergence** | {'PASS' if a.get('gates', {}).get('coupled_convergence_pass') else 'FAIL'} | {'PASS' if b.get('gates', {}).get('coupled_convergence_pass') else 'FAIL'} | - |",
        f"| **Reaction Force Drift** | {rf_drift_a_txt} | {rf_drift_b_txt} | Tol: <= 2.0% |",
        f"| **Total Energy Drift** | {e_drift_a_txt} | {e_drift_b_txt} | Tol: <= 2.0% |",
        f"| **Overall Physical Acceptance** | {'PASS' if a.get('gates', {}).get('overall_physical_acceptance_pass') else 'FAIL'} | {'PASS' if b.get('gates', {}).get('overall_physical_acceptance_pass') else 'FAIL'} | - |",
        "",
        "---",
        "",
        "## 2. Scientific Verdict & Next Actions",
        "",
    ]

    if cmp.get("arm_b_accelerated_convergence"):
        lines.append("- **DECISIVE ACCELERATION PROVEN:** Safeguarded Anderson acceleration (Arm B) achieved coupled re-equilibration where Picard baseline (Arm A) stagnated/failed.")
        lines.append("- **ACTION:** Register Arm B state as accepted C6 Checkpoint 04 and proceed to forward continuation step.")
    elif cmp.get("both_arms_coupled_converged"):
        lines.append("- **BOTH ARMS CONVERGED:** Isoparametric transfer resolved the nonmatching disequilibrium.")
        lines.append("- **ACTION:** Compare efficiency factor and select optimal configuration for forward continuation.")
    else:
        lines.append("- **COUPLED NONCONVERGENCE PRESERVED:** Neither arm satisfied the strict coupled convergence thresholds in 140 iterations.")
        lines.append("- **ACTION:** Inspect asymptotic contraction factors and formulate bounded Stage 2 / Anderson parameter optimization.")

    return "\n".join(lines)


def evaluate(
    dir_174: Path,
    dir_175: Path,
    job_174: str = "1420391.mmaster02",
    job_175: str = "1420392.mmaster02",
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Main evaluation routine."""
    if out_dir is None:
        out_dir = REPO_ROOT / "results" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Telemetry and endpoints
    t174 = load_telemetry(dir_174 / "live_iteration_telemetry.json")
    t175 = load_telemetry(dir_175 / "live_iteration_telemetry.json")

    ep174 = load_endpoint_or_checkpoint(dir_174)
    ep175 = load_endpoint_or_checkpoint(dir_175)

    # 2. Analyze arms
    arm_a = analyze_arm("Arm A (Picard Baseline)", "174_c6_r12_picard_baseline", job_174, t174, ep174)
    arm_b = analyze_arm("Arm B (Anderson M2)", "175_c6_r12_anderson_m2", job_175, t175, ep175)

    # 3. Compare
    comparison = compare_arms(arm_a, arm_b)

    summary = {
        "task_id": "F1629-METHOD-C-C6-R12-OVERNIGHT-CONTROLLED-PAIR",
        "timestamp": "2026-11-05T20:50:00+01:00",
        "arm_a_picard": arm_a,
        "arm_b_anderson": arm_b,
        "comparison": comparison,
    }

    # 4. Write artifacts
    json_path = out_dir / "f1629_paired_execution_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    md_report = generate_markdown_report(summary)
    md_path = out_dir / "f1629_paired_execution_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    return summary


if __name__ == "__main__":
    p174 = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline")
    p175 = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2")
    res = evaluate(p174, p175)
    print("Evaluation completed successfully.")
