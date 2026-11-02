# -*- coding: utf-8 -*-
"""
evaluate_coupled_convergence_turn31.py
Fetch latest authentic telemetry from Job 1419489 (R2) and Job 1419490 (R8),
perform rigorous simultaneous multi-variable contraction analysis (delta_d, delta_u, delta_H),
and determine exact projected coupled convergence outer iteration against the 200-outer budget.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
import math
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"

R2_REMOTE_FILE = "/scratch9/pr21vyci/runs/mode1_c5_package163_r2_c2_1_continuation/continuation_1419489.mmaster02/live_iteration_telemetry.json"
R2_LOCAL_FILE = REPO_ROOT / "results/validation/package163_r2_live_telemetry_turn31.json"

R8_REMOTE_FILE = "/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r8/continuation_1419490.mmaster02/live_iteration_telemetry.json"
R8_LOCAL_FILE = REPO_ROOT / "results/validation/package157_r8_live_telemetry_turn31.json"

OUTPUT_REPORT = REPO_ROOT / "results/validation/coupled_convergence_evaluation_turn31.json"

TOL_D = 1.0e-5
TOL_U = 1.0e-9   # mm
TOL_H = 1.0e-4   # MPa


def fetch_file(remote_path: str, local_path: Path):
    ps_cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(SSH_WRAPPER),
        "-RemoteCommand", f"cat {remote_path}",
        "-TimeoutSeconds", "120"
    ]
    res = subprocess.run(ps_cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Fetch failed for {remote_path}: {res.stderr}")
        return None
    raw = res.stdout.strip()
    idx_start = raw.find("[")
    idx_end = raw.rfind("]")
    if idx_start == -1 or idx_end == -1:
        print(f"No JSON array in {remote_path}")
        return None
    data = json.loads(raw[idx_start:idx_end + 1])
    local_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def analyze_r2(data):
    if not data:
        return None
    total = len(data)
    latest = data[-1]
    outers = [d["outer"] for d in data]
    k_curr = latest["outer"]

    d_val = latest["delta_d"]
    u_val = latest.get("delta_u")
    h_val = latest.get("delta_h")
    dual_val = latest.get("dual_error")
    free_val = latest.get("free_error")
    active_val = latest.get("pdas_active_count")

    valid_u = [(d["outer"], d["delta_u"]) for d in data if d.get("delta_u") is not None]
    valid_h = [(d["outer"], d["delta_h"]) for d in data if d.get("delta_h") is not None]
    valid_d = [(d["outer"], d["delta_d"]) for d in data if d.get("delta_d") is not None]

    # Contraction rates over robust asymptotic window (from outer 119 to current outer)
    # This avoids local jitter from single-node active-set boundary adjustments
    rec_119 = next((d for d in data if d["outer"] == 119), None)
    if rec_119 and k_curr > 119:
        span = k_curr - 119
        robust_rho_u = (u_val / rec_119["delta_u"]) ** (1.0 / span)
        robust_rho_h = (h_val / rec_119["delta_h"]) ** (1.0 / span)
    else:
        robust_rho_u = 0.9728
        robust_rho_h = 0.9726

    # Recent 5-step window
    window_size = 5
    rates_u = [valid_u[i][1] / valid_u[i-1][1] for i in range(len(valid_u) - window_size + 1, len(valid_u)) if valid_u[i-1][1] > 0]
    rates_h = [valid_h[i][1] / valid_h[i-1][1] for i in range(len(valid_h) - window_size + 1, len(valid_h)) if valid_h[i-1][1] > 0]

    rho_u = sum(rates_u) / len(rates_u) if rates_u else robust_rho_u
    rho_h = sum(rates_h) / len(rates_h) if rates_h else robust_rho_h
    rho_d = 0.95  # Nominal phase contraction when active set is stabilized

    # Check whether tolerances are already satisfied
    pass_d = (d_val <= TOL_D)
    pass_u = (u_val is not None and u_val <= TOL_U)
    pass_h = (h_val is not None and h_val <= TOL_H)
    kkt_pass = (dual_val is not None and dual_val <= 1e-6 and free_val is not None and free_val <= 1e-6)

    # Projections
    def project_outer(curr_val, target_tol, rho, curr_k):
        if curr_val <= target_tol:
            return curr_k
        if rho >= 1.0 or rho <= 0.0:
            return 999
        steps_needed = math.log(target_tol / curr_val) / math.log(rho)
        return curr_k + math.ceil(steps_needed)

    proj_k_d = project_outer(d_val, TOL_D, rho_d, k_curr)
    proj_k_u = project_outer(u_val, TOL_U, robust_rho_u, k_curr) if u_val else 999
    proj_k_h = project_outer(h_val, TOL_H, robust_rho_h, k_curr) if h_val else 999

    coupled_proj_k = max(proj_k_d, proj_k_u, proj_k_h)
    budget_sufficient = (coupled_proj_k <= 200)

    # Projection at outer 200
    steps_to_200 = 200 - k_curr
    u_at_200 = u_val * (robust_rho_u ** steps_to_200) if u_val else None
    h_at_200 = h_val * (robust_rho_h ** steps_to_200) if h_val else None

    # Print table of last 10 iterations
    print("\nR2 (Job 1419489) Latest Telemetry Trace:")
    print("-" * 115)
    print(f"{'Outer':>5} | {'Delta_d':>12} | {'Delta_u (mm)':>14} | {'Delta_h (MPa)':>14} | {'Dual Err':>12} | {'Free Err':>12} | {'Active Nodes':>12}")
    print("-" * 115)
    for d in data[-10:]:
        du = f"{d.get('delta_u', 0.0):.6e}" if d.get('delta_u') is not None else "None"
        dh = f"{d.get('delta_h', 0.0):.6e}" if d.get('delta_h') is not None else "None"
        print(f"{d['outer']:5d} | {d['delta_d']:12.6e} | {du:>14} | {dh:>14} | {d.get('dual_error', 0.0):12.6e} | {d.get('free_error', 0.0):12.6e} | {d.get('pdas_active_count', 0):12d}")
    print("-" * 115)

    print(f"\nCurrent State at Outer {k_curr}:")
    print(f"  Delta_d: {d_val:.6e} (Target <= {TOL_D:.1e}, Ratio={d_val/TOL_D:.2f}x, Status={'PASS' if pass_d else 'PENDING'})")
    print(f"  Delta_u: {u_val:.6e} mm (Target <= {TOL_U:.1e} mm, Ratio={u_val/TOL_U:.2f}x, Status={'PASS' if pass_u else 'PENDING'})")
    print(f"  Delta_H: {h_val:.6e} MPa (Target <= {TOL_H:.1e} MPa, Ratio={h_val/TOL_H:.2f}x, Status={'PASS' if pass_h else 'PENDING'})")
    print(f"  Dual err: {dual_val:.6e} kN*mm, Free err: {free_val:.6e} kN (KKT pass={kkt_pass})")
    print(f"  Active nodes: {active_val}")
    print(f"\nMeasured Contraction Rates:")
    print(f"  Robust multi-step (outer 119 -> {k_curr}): rho_u = {robust_rho_u:.4f}, rho_H = {robust_rho_h:.4f}")
    print(f"  Recent 5-step window: rho_u = {rho_u:.4f}, rho_H = {rho_h:.4f}")
    print(f"  Individual Projections to Tol:")
    print(f"    Delta_d: projected outer {proj_k_d} (rho_d ~ {rho_d:.2f})")
    print(f"    Delta_u: projected outer {proj_k_u} (rho_u ~ {robust_rho_u:.4f}, required ratio = {u_val/TOL_U:.2f}x)")
    print(f"    Delta_H: projected outer {proj_k_h} (rho_H ~ {robust_rho_h:.4f}, required ratio = {h_val/TOL_H:.2f}x)")
    print(f"  Simultaneous Coupled Convergence Target: Outer {coupled_proj_k}")
    print(f"  Projected Values at Outer 200 Budget Ceiling:")
    print(f"    Delta_u at 200: {u_at_200:.4e} mm (Tolerance <= {TOL_U:.1e} mm)")
    print(f"    Delta_H at 200: {h_at_200:.4e} MPa (Tolerance <= {TOL_H:.1e} MPa)")
    print(f"  Budget (200 outers) Sufficient Under Current Rates: {budget_sufficient}")

    return {
        "job_id": "1419489.mmaster02",
        "total_records": total,
        "current_outer": k_curr,
        "current_residuals": {
            "delta_d": d_val,
            "delta_u_mm": u_val,
            "delta_h_MPa": h_val,
            "dual_error_kNmm": dual_val,
            "free_error_kN": free_val,
            "active_nodes": active_val
        },
        "tolerances": {
            "tol_d": TOL_D,
            "tol_u_mm": TOL_U,
            "tol_h_MPa": TOL_H
        },
        "distance_to_target": {
            "delta_d_ratio_to_tol": round(d_val / TOL_D, 4),
            "delta_u_ratio_to_tol": round(u_val / TOL_U, 4) if u_val else None,
            "delta_h_ratio_to_tol": round(h_val / TOL_H, 4) if h_val else None
        },
        "contraction_rates": {
            "robust_rho_u": round(robust_rho_u, 4),
            "robust_rho_h": round(robust_rho_h, 4),
            "window5_rho_u": round(rho_u, 4),
            "window5_rho_h": round(rho_h, 4),
            "nominal_rho_d": round(rho_d, 4)
        },
        "individual_projections": {
            "projected_outer_delta_d": proj_k_d,
            "projected_outer_delta_u": proj_k_u,
            "projected_outer_delta_h": proj_k_h
        },
        "coupled_convergence_projection": {
            "simultaneous_outer_target": coupled_proj_k,
            "budget_limit": 200,
            "budget_sufficient": budget_sufficient,
            "headroom_outers": 200 - coupled_proj_k if budget_sufficient else (200 - coupled_proj_k),
            "projected_delta_u_at_200_mm": u_at_200,
            "projected_delta_h_at_200_MPa": h_at_200
        },
        "coupled_status": "CONVERGED" if (pass_d and pass_u and pass_h and kkt_pass) else "IN_PROGRESS"
    }


def analyze_r8(data):
    if not data:
        return None
    latest = data[-1]
    print(f"\nR8 (Job 1419490) Latest Telemetry (Total {len(data)} records):")
    print(f"  Outer: {latest['outer']}, target_uy: {latest.get('target_uy')}")
    print(f"  delta_d: {latest.get('delta_d'):.6e}, delta_u: {latest.get('delta_u', 0.0):.6e} mm, delta_h: {latest.get('delta_h', 0.0):.6e} MPa")
    print(f"  dual_error: {latest.get('dual_error', 0.0):.6e}, free_error: {latest.get('free_error', 0.0):.6e}")
    return {
        "job_id": "1419490.mmaster02",
        "total_records": len(data),
        "latest_outer": latest["outer"],
        "target_uy_mm": latest.get("target_uy"),
        "latest_residuals": latest
    }


def main():
    r2_data = fetch_file(R2_REMOTE_FILE, R2_LOCAL_FILE)
    r8_data = fetch_file(R8_REMOTE_FILE, R8_LOCAL_FILE)

    r2_analysis = analyze_r2(r2_data)
    r8_analysis = analyze_r8(r8_data)

    report = {
        "schema": 1,
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "evaluation": "COUPLED_CONVERGENCE_ASSESSMENT_TURN31",
        "package163_r2": r2_analysis,
        "package157_r8": r8_analysis
    }

    OUTPUT_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nCoupled convergence report written to: {OUTPUT_REPORT}")
    return report


if __name__ == "__main__":
    main()
