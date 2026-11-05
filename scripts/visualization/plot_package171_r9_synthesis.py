#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_package171_r9_synthesis.py
Plots comprehensive 3-job convergence synthesis comparing R7 (100 iters, constant S1),
R8 (140 iters, false-positive rollback trap), and R9 (Job 1420215, unrelaxed step norm).
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R7_TELEMETRY = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r7_c3_0_adaptive_reequilibration/evidence/1419873.mmaster02/live_iteration_telemetry.json"
R8_TELEMETRY = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration/evidence/1420188.mmaster02/live_iteration_telemetry.json"
OUTPUT_DIR = REPO_ROOT / "results/figures/mode1_package171"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def plot_three_way_synthesis(r9_data: list[dict]):
    with open(R7_TELEMETRY, "r", encoding="utf-8") as f:
        r7_data = json.load(f)
    with open(R8_TELEMETRY, "r", encoding="utf-8") as f:
        r8_data = json.load(f)

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

    fig, axes = plt.subplots(2, 2, figsize=(13, 10), dpi=300)
    plt.subplots_adjust(hspace=0.28, wspace=0.25)

    # (a) Damage increment
    ax = axes[0, 0]
    ax.plot(r7_iter, r7_dd, color="#D95F02", linestyle=":", linewidth=1.5, label="R7 (PBS 1419873, 100 iters)")
    ax.plot(r8_iter, r8_dd, color="#7570B3", linestyle="--", linewidth=1.5, label="R8 (PBS 1420188, 140 iters)")
    ax.plot(r9_iter, r9_dd, color="#1B9E77", linewidth=2.2, label=f"R9 (PBS 1420215, {len(r9_iter)} iters)")
    ax.axhline(1e-5, color="black", linestyle="-.", linewidth=1.5, label=r"Tolerance $\Delta d \leq 10^{-5}$")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Damage Increment $\Delta d$", fontsize=11, fontweight="bold")
    ax.set_title(r"(a) Phase-Field Damage Convergence $\|\Delta d\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    # (b) Mechanical displacement increment
    ax = axes[0, 1]
    ax.plot(r7_iter[:len(r7_du)], r7_du, color="#D95F02", linestyle=":", linewidth=1.5, label="R7 (PBS 1419873)")
    ax.plot(r8_iter[:len(r8_du)], r8_du, color="#7570B3", linestyle="--", linewidth=1.5, label="R8 (PBS 1420188)")
    ax.plot(r9_iter[:len(r9_du)], r9_du, color="#1B9E77", linewidth=2.2, label="R9 (PBS 1420215)")
    ax.axhline(1e-9, color="black", linestyle="-.", linewidth=1.5, label=r"Tolerance $\Delta u \leq 10^{-9}$ mm")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Displacement Increment $\Delta u$ [mm]", fontsize=11, fontweight="bold")
    ax.set_title(r"(b) Mechanical Displacement Convergence $\|\Delta u\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    # (c) Driving history increment
    ax = axes[1, 0]
    ax.plot(r7_iter[:len(r7_dh)], r7_dh, color="#D95F02", linestyle=":", linewidth=1.5, label="R7 (PBS 1419873)")
    ax.plot(r8_iter[:len(r8_dh)], r8_dh, color="#7570B3", linestyle="--", linewidth=1.5, label="R8 (PBS 1420188)")
    ax.plot(r9_iter[:len(r9_dh)], r9_dh, color="#1B9E77", linewidth=2.2, label="R9 (PBS 1420215)")
    ax.axhline(1e-4, color="black", linestyle="-.", linewidth=1.5, label=r"Tolerance $\Delta H \leq 10^{-4}$ MPa")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Driving History Increment $\Delta H$ [MPa]", fontsize=11, fontweight="bold")
    ax.set_title(r"(c) History Variable Convergence $\|\Delta H\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    # (d) Active set cardinality
    ax = axes[1, 1]
    ax.plot(r7_iter, r7_act, color="#D95F02", linestyle=":", linewidth=1.5, label="R7 Active Nodes")
    ax.plot(r8_iter, r8_act, color="#7570B3", linestyle="--", linewidth=1.5, label="R8 Active Nodes")
    ax.plot(r9_iter, r9_act, color="#1B9E77", linewidth=2.2, label="R9 Active Nodes")
    ax.axhline(500, color="gray", linestyle="-.", linewidth=1.5, label=r"Stage 2 Threshold $|A_k| \leq 500$")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel("Active Node Count $|A_k|$", fontsize=11, fontweight="bold")
    ax.set_title(r"(d) Active-Set Cardinality Contraction $|A_k|$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    fig_png = OUTPUT_DIR / "fig_p171_r7_vs_r8_vs_r9_coupled_convergence.png"
    fig_pdf = OUTPUT_DIR / "fig_p171_r7_vs_r8_vs_r9_coupled_convergence.pdf"
    plt.savefig(fig_png, dpi=300, bbox_inches="tight")
    plt.savefig(fig_pdf, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fig_png.name} and {fig_pdf.name}")

if __name__ == "__main__":
    import sys
    telemetry_path = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r9_c3_0_adaptive_reequilibration/evidence/1420215.mmaster02/live_iteration_telemetry.json"
    if telemetry_path.exists():
        with open(telemetry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        plot_three_way_synthesis(data)
    else:
        print("Waiting for live telemetry file...")
