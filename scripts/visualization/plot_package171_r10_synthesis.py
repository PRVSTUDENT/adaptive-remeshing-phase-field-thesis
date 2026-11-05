#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_package171_r10_synthesis.py
================================
Plots comprehensive 4-job convergence synthesis comparing:
- R7 (PBS 1419873, 100 iters, constant Stage 1 omega_d = 0.50, omega_u = 1.0)
- R8 (PBS 1420188, 140 iters, false-positive rollback trap)
- R9 (PBS 1420215, 140 iters, unrelaxed step norm, sustained omega_d = 0.85, omega_u = 1.0)
- R10 (PBS 1420261, 140 iters, isolated mechanical displacement under-relaxation omega_u = 0.85)
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R7_TELEMETRY = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r7_c3_0_adaptive_reequilibration/evidence/1419873.mmaster02/live_iteration_telemetry.json"
R8_TELEMETRY = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration/evidence/1420188.mmaster02/live_iteration_telemetry.json"
R9_TELEMETRY = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r9_c3_0_adaptive_reequilibration/evidence/1420215.mmaster02/live_iteration_telemetry.json"
OUTPUT_DIR = REPO_ROOT / "results/figures/mode1_package171"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def plot_four_way_synthesis(r10_data: list):
    with open(R7_TELEMETRY, "r", encoding="utf-8") as f:
        r7_data = json.load(f)
    with open(R8_TELEMETRY, "r", encoding="utf-8") as f:
        r8_data = json.load(f)
    with open(R9_TELEMETRY, "r", encoding="utf-8") as f:
        r9_data = json.load(f)

    r7_iter = [x["outer"] for x in r7_data]
    r7_dd = [x["delta_d"] for x in r7_data]
    r7_du = [x["delta_u"] for x in r7_data if x["delta_u"] is not None]
    r7_dh = [x["delta_h"] for x in r7_data if x["delta_h"] is not None]
    r7_act = [x["pdas_active_count"] for x in r7_data]

    r8_iter = [x["outer"] for x in r8_data]
    r8_dd = [x["delta_d"] for x in r8_data]
    r8_du = [x["delta_u"] for x in r8_data if x["delta_u"] is not None]
    r8_dh = [x["delta_h"] for x in r8_data if x["delta_h"] is not None]
    r8_act = [x["pdas_active_count"] for x in r8_data]

    r9_iter = [x["outer"] for x in r9_data]
    r9_dd = [x["delta_d"] for x in r9_data]
    r9_du = [x["delta_u"] for x in r9_data if x.get("delta_u") is not None]
    r9_dh = [x["delta_h"] for x in r9_data if x.get("delta_h") is not None]
    r9_act = [x["pdas_active_count"] for x in r9_data]

    r10_iter = [x["outer"] for x in r10_data]
    r10_dd = [x["delta_d"] for x in r10_data]
    r10_du_raw = [x.get("delta_u_raw", x.get("delta_u")) for x in r10_data if x.get("delta_u_raw", x.get("delta_u")) is not None]
    r10_du_rel = [x.get("delta_u_relaxed", x.get("delta_u")) for x in r10_data if x.get("delta_u_relaxed", x.get("delta_u")) is not None]
    r10_dh = [x["delta_h"] for x in r10_data if x.get("delta_h") is not None]
    r10_act = [x["pdas_active_count"] for x in r10_data]

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=300)
    plt.subplots_adjust(hspace=0.28, wspace=0.25)

    # (a) Damage increment
    ax = axes[0, 0]
    ax.plot(r7_iter, r7_dd, color="#999999", linestyle=":", linewidth=1.2, label="R7 (PBS 1419873, S1 only)")
    ax.plot(r8_iter, r8_dd, color="#D95F02", linestyle="--", linewidth=1.2, label="R8 (PBS 1420188, RB trap)")
    ax.plot(r9_iter, r9_dd, color="#7570B3", linestyle="-.", linewidth=1.5, label="R9 (PBS 1420215, S2 unrelaxed)")
    ax.plot(r10_iter, r10_dd, color="#1B9E77", linewidth=2.2, label=f"R10 (PBS 1420261, $\\omega_u=0.85$)")
    ax.axhline(1e-5, color="black", linestyle="-", linewidth=1.5, label=r"Tol $\Delta d \leq 10^{-5}$")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Damage Increment $\Delta d$", fontsize=11, fontweight="bold")
    ax.set_title(r"(a) Phase-Field Damage Convergence $\|\Delta d\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=8.5)
    ax.set_xlim(0, 145)

    # (b) Mechanical displacement increment
    ax = axes[0, 1]
    ax.plot(r7_iter[:len(r7_du)], r7_du, color="#999999", linestyle=":", linewidth=1.2, label="R7 (PBS 1419873)")
    ax.plot(r8_iter[:len(r8_du)], r8_du, color="#D95F02", linestyle="--", linewidth=1.2, label="R8 (PBS 1420188)")
    ax.plot(r9_iter[:len(r9_du)], r9_du, color="#7570B3", linestyle="-.", linewidth=1.5, label="R9 (PBS 1420215)")
    ax.plot(r10_iter[:len(r10_du_raw)], r10_du_raw, color="#1B9E77", linewidth=2.0, label=r"R10 Raw $\Delta u_{\mathrm{raw}}$")
    if len(r10_du_rel) > 0:
        ax.plot(r10_iter[:len(r10_du_rel)], r10_du_rel, color="#E7298A", linewidth=1.5, linestyle="--", label=r"R10 Rel $\Delta u_{\mathrm{rel}}$")
    ax.axhline(1e-9, color="black", linestyle="-", linewidth=1.5, label=r"Tol $\Delta u \leq 10^{-9}$ mm")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Displacement Increment $\Delta u$ [mm]", fontsize=11, fontweight="bold")
    ax.set_title(r"(b) Mechanical Displacement Convergence $\|\Delta u\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=8.5)
    ax.set_xlim(0, 145)

    # (c) Driving history increment
    ax = axes[1, 0]
    ax.plot(r7_iter[:len(r7_dh)], r7_dh, color="#999999", linestyle=":", linewidth=1.2, label="R7 (PBS 1419873)")
    ax.plot(r8_iter[:len(r8_dh)], r8_dh, color="#D95F02", linestyle="--", linewidth=1.2, label="R8 (PBS 1420188)")
    ax.plot(r9_iter[:len(r9_dh)], r9_dh, color="#7570B3", linestyle="-.", linewidth=1.5, label="R9 (PBS 1420215)")
    ax.plot(r10_iter[:len(r10_dh)], r10_dh, color="#1B9E77", linewidth=2.2, label="R10 (PBS 1420261)")
    ax.axhline(1e-4, color="black", linestyle="-", linewidth=1.5, label=r"Tol $\Delta H \leq 10^{-4}$ MPa")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Driving History Increment $\Delta H$ [MPa]", fontsize=11, fontweight="bold")
    ax.set_title(r"(c) History Variable Convergence $\|\Delta H\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=8.5)
    ax.set_xlim(0, 145)

    # (d) Active set cardinality
    ax = axes[1, 1]
    ax.plot(r7_iter, r7_act, color="#999999", linestyle=":", linewidth=1.2, label="R7 Active Nodes")
    ax.plot(r8_iter, r8_act, color="#D95F02", linestyle="--", linewidth=1.2, label="R8 Active Nodes")
    ax.plot(r9_iter, r9_act, color="#7570B3", linestyle="-.", linewidth=1.5, label="R9 Active Nodes")
    ax.plot(r10_iter, r10_act, color="#1B9E77", linewidth=2.2, label="R10 Active Nodes")
    ax.axhline(500, color="gray", linestyle="-.", linewidth=1.5, label=r"Stage 2 Threshold $|A_k| \leq 500$")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel("Active Node Count $|A_k|$", fontsize=11, fontweight="bold")
    ax.set_title(r"(d) Active-Set Cardinality Contraction $|A_k|$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=8.5)
    ax.set_xlim(0, 145)

    fig.suptitle(f"Package 171 Re-Equilibration Synthesis: R7 vs R8 vs R9 vs R10\nEffect of Isolated Displacement Under-Relaxation ($\\omega_u=0.85$)", fontsize=14, fontweight="bold", y=0.98)

    out_png = OUTPUT_DIR / "package171_r10_four_way_synthesis.png"
    out_pdf = OUTPUT_DIR / "package171_r10_four_way_synthesis.pdf"
    plt.savefig(out_png, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()
    print(f"Saved synthesis plots:\n  {out_png}\n  {out_pdf}")

if __name__ == "__main__":
    import sys
    telemetry_path = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02/live_iteration_telemetry.json"
    if len(sys.argv) > 1:
        telemetry_path = Path(sys.argv[1])
    if not telemetry_path.exists():
        print(f"Telemetry file not found: {telemetry_path}")
        sys.exit(1)
    with open(telemetry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    plot_four_way_synthesis(data)
