#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_package171_convergence_synthesis.py
=========================================
Generates publication-quality figures evaluating Package 171-R7 and R8 coupled
PDAS re-equilibration dynamics, active-set evolution, KKT stationarity, and
the Stage 2 relaxation-switching false-positive rollback mechanism.

Outputs:
- results/figures/mode1_package171/fig_p171_r7_vs_r8_coupled_convergence.png / .pdf
- results/figures/mode1_package171/fig_p171_r8_transition_and_rollback_dynamics.png / .pdf
"""

from __future__ import annotations

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
R7_TELEMETRY = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r7_c3_0_adaptive_reequilibration/evidence/1419873.mmaster02/live_iteration_telemetry.json"
R8_TELEMETRY = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration/evidence/1420188.mmaster02/live_iteration_telemetry.json"
REPLAY_FILE = REPO_ROOT / "results/validation/package171_r8_authentic_rollback_replay.json"
OUTPUT_DIR = REPO_ROOT / "results/figures/mode1_package171"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_telemetry(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_convergence_comparison(r7_data: list[dict], r8_data: list[dict]):
    print("Generating Figure 1: R7 vs R8 Coupled Convergence Comparison...")
    
    r7_iter = [x["outer"] for x in r7_data]
    r7_dd = [x["delta_d"] for x in r7_data]
    r7_du = [x["delta_u"] for x in r7_data]
    r7_dh = [x["delta_h"] for x in r7_data]
    r7_act = [x["pdas_active_count"] for x in r7_data]

    r8_iter = [x["outer"] for x in r8_data]
    r8_dd = [x["delta_d"] for x in r8_data]
    r8_du = [x["delta_u"] for x in r8_data]
    r8_dh = [x["delta_h"] for x in r8_data]
    r8_act = [x["pdas_active_count"] for x in r8_data]

    fig, axes = plt.subplots(2, 2, figsize=(12, 10), dpi=300)
    plt.subplots_adjust(hspace=0.28, wspace=0.25)

    # (a) Damage increment
    ax = axes[0, 0]
    ax.plot(r7_iter, r7_dd, color="#D95F02", linestyle="--", linewidth=1.8, label="R7 (PBS 1419873, 100 iters)")
    ax.plot(r8_iter, r8_dd, color="#1B9E77", linewidth=2.0, label="R8 (PBS 1420188, 140 iters)")
    ax.axhline(1e-5, color="black", linestyle=":", linewidth=1.5, label=r"Tolerance $\Delta d \leq 10^{-5}$")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Damage Increment $\Delta d$", fontsize=11, fontweight="bold")
    ax.set_title(r"(a) Phase-Field Damage Convergence $\|\Delta d\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    # (b) Displacement increment
    ax = axes[0, 1]
    ax.plot(r7_iter, r7_du, color="#D95F02", linestyle="--", linewidth=1.8, label="R7 (PBS 1419873)")
    ax.plot(r8_iter, r8_du, color="#1B9E77", linewidth=2.0, label="R8 (PBS 1420188)")
    ax.axhline(1e-9, color="black", linestyle=":", linewidth=1.5, label=r"Tolerance $\Delta u \leq 10^{-9}$ mm")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Displacement Increment $\Delta u$ [mm]", fontsize=11, fontweight="bold")
    ax.set_title(r"(b) Mechanical Displacement Convergence $\|\Delta u\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    # (c) Driving history increment
    ax = axes[1, 0]
    ax.plot(r7_iter, r7_dh, color="#D95F02", linestyle="--", linewidth=1.8, label="R7 (PBS 1419873)")
    ax.plot(r8_iter, r8_dh, color="#1B9E77", linewidth=2.0, label="R8 (PBS 1420188)")
    ax.axhline(1e-4, color="black", linestyle=":", linewidth=1.5, label=r"Tolerance $\Delta H \leq 10^{-4}$ MPa")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Driving History Increment $\Delta H$ [MPa]", fontsize=11, fontweight="bold")
    ax.set_title(r"(c) History Variable Convergence $\|\Delta H\|_\infty$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    # (d) Active set cardinality
    ax = axes[1, 1]
    ax.plot(r7_iter, r7_act, color="#D95F02", linestyle="--", linewidth=1.8, label="R7 Active Nodes")
    ax.plot(r8_iter, r8_act, color="#1B9E77", linewidth=2.0, label="R8 Active Nodes")
    ax.axhline(500, color="#7570B3", linestyle=":", linewidth=1.5, label=r"Stage 2 Threshold $|A_k| \leq 500$")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel("Active Node Count $|A_k|$", fontsize=11, fontweight="bold")
    ax.set_title(r"(d) Active-Set Cardinality Contraction $|A_k|$", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    fig_png = OUTPUT_DIR / "fig_p171_r7_vs_r8_coupled_convergence.png"
    fig_pdf = OUTPUT_DIR / "fig_p171_r7_vs_r8_coupled_convergence.pdf"
    plt.savefig(fig_png, dpi=300, bbox_inches="tight")
    plt.savefig(fig_pdf, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fig_png.name} and {fig_pdf.name}")


def plot_transition_dynamics(r8_data: list[dict], replay_data: dict):
    print("Generating Figure 2: R8 Transition and Rollback Dynamics Analysis...")
    
    iters = [x["outer"] for x in r8_data]
    card = [x["pdas_active_count"] for x in r8_data]
    sym_diff = [x["active_set_symmetric_diff"] for x in r8_data]
    added = [x["added_nodes_count"] for x in r8_data]
    omega = [x["effective_omega_d"] for x in r8_data]
    free_err = [x["free_error"] for x in r8_data]
    dual_err = [x["dual_error"] for x in r8_data]

    transitions = replay_data["transitions"]
    trans_iters = [t["outer_iteration"] for t in transitions]
    relaxed_ratios = [t["r8_relaxed_ratio"] for t in transitions]
    raw_ratios = [t["r9_raw_ratio"] for t in transitions]

    fig, axes = plt.subplots(2, 2, figsize=(13, 10), dpi=300)
    plt.subplots_adjust(hspace=0.30, wspace=0.28)

    # (a) Active-set stability metrics in tail regime (k >= 50)
    ax1 = axes[0, 0]
    tail_mask = [i >= 50 for i in iters]
    tail_iters = [iters[i] for i, m in enumerate(tail_mask) if m]
    tail_card = [card[i] for i, m in enumerate(tail_mask) if m]
    tail_sym = [sym_diff[i] for i, m in enumerate(tail_mask) if m]
    tail_add = [added[i] for i, m in enumerate(tail_mask) if m]

    color = "#1B9E77"
    ax1.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Active Set Cardinality $|A_k|$", color=color, fontsize=11, fontweight="bold")
    line1 = ax1.plot(tail_iters, tail_card, color=color, linewidth=2.0, label="Cardinality $|A_k|$")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_ylim(0, 1400)
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    color2 = "#7570B3"
    ax2.set_ylabel(r"Symmetric Difference $|\Delta A_k|$", color=color2, fontsize=11, fontweight="bold")
    line2 = ax2.plot(tail_iters, tail_sym, color=color2, linestyle="-.", linewidth=1.8, label=r"$|\Delta A_k|$")
    line3 = ax2.plot(tail_iters, tail_add, color="#E7298A", linestyle=":", linewidth=1.8, label=r"Newly Added $\Delta A^+$")
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(-1, 35)

    # Mark the Outer 89 trigger
    ax1.axvline(89, color="#E41A1C", linestyle="--", alpha=0.8, linewidth=1.5)
    ax1.text(90, 800, "Outer 89:\nStage 2 Trigger", color="#E41A1C", fontsize=9, fontweight="bold")
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper right", frameon=True, fontsize=8.5)
    ax1.set_title(r"(a) Active-Set Stabilization ($k \geq 50$)", fontsize=12, fontweight="bold")

    # (b) Effective relaxation factor
    ax = axes[0, 1]
    ax.plot(iters, omega, color="#2166AC", linewidth=2.0, label=r"Committed $\omega_d$")
    ax.scatter(trans_iters, [0.85] * len(trans_iters), color="#E41A1C", marker="^", s=45, zorder=5, label="Attempted S2 (0.85)")
    ax.scatter(trans_iters, [0.50] * len(trans_iters), color="#B2182B", marker="v", s=45, zorder=5, label="Rollback to S1 (0.50)")
    ax.set_ylim(0.40, 0.95)
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Relaxation Parameter $\omega_d$", fontsize=11, fontweight="bold")
    ax.set_title(r"(b) Two-Phase Relaxation Trapping (18 Rollbacks)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="center right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    # (c) Step Increment Ratio Contrast (R8 Relaxed vs R9 Raw)
    ax = axes[1, 0]
    bar_x = np.arange(len(trans_iters))
    width = 0.38
    ax.bar(bar_x - width/2, relaxed_ratios, width, color="#D95F02", alpha=0.85, label=r"R8 Relaxed Ratio: $\frac{\omega_2 \|\delta d_{cand}\|}{\omega_1 \|\delta d_{prev}\|}$")
    ax.bar(bar_x + width/2, raw_ratios, width, color="#1B9E77", alpha=0.85, label=r"R9 Raw Norm Ratio: $\frac{\|\delta d_{cand}\|}{\|\delta d_{prev}\|}$")
    ax.axhline(1.50, color="#E41A1C", linestyle="--", linewidth=1.5, label="R8 Divergence Threshold (1.50)")
    ax.axhline(1.00, color="black", linestyle=":", linewidth=1.2, label="Strict Contraction Bound (1.00)")
    ax.set_xticks(bar_x[::2])
    ax.set_xticklabels([str(t) for t in trans_iters[::2]], fontsize=8.5)
    ax.set_xlabel("Outer Iteration of Transition Attempt", fontsize=11, fontweight="bold")
    ax.set_ylabel("Candidate Step Ratio", fontsize=11, fontweight="bold")
    ax.set_title(r"(c) Rollback Mechanism Contrast Across All 18 Transitions", fontsize=12, fontweight="bold")
    ax.set_ylim(0.8, 1.85)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower left", frameon=True, fontsize=8.5)

    # (d) KKT stationarity error
    ax = axes[1, 1]
    ax.plot(iters, free_err, color="#377EB8", linewidth=1.8, label=r"Free Node Residual $\|R_d^{\text{free}}\|_\infty$")
    ax.plot(iters, dual_err, color="#4DAF4A", linewidth=1.8, label=r"Dual Complementarity Residual $\|R_d^{\text{dual}}\|_\infty$")
    ax.axhline(1e-6, color="black", linestyle=":", linewidth=1.5, label=r"KKT Tolerance $10^{-6}$")
    ax.set_yscale("log")
    ax.set_xlabel("Outer Iteration $k$", fontsize=11, fontweight="bold")
    ax.set_ylabel("KKT Stationarity Error", fontsize=11, fontweight="bold")
    ax.set_title(r"(d) Variational KKT Complementarity Admissibility", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.set_xlim(0, 145)

    fig_png = OUTPUT_DIR / "fig_p171_r8_transition_and_rollback_dynamics.png"
    fig_pdf = OUTPUT_DIR / "fig_p171_r8_transition_and_rollback_dynamics.pdf"
    plt.savefig(fig_png, dpi=300, bbox_inches="tight")
    plt.savefig(fig_pdf, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fig_png.name} and {fig_pdf.name}")


def main():
    r7_data = load_telemetry(R7_TELEMETRY)
    r8_data = load_telemetry(R8_TELEMETRY)
    with open(REPLAY_FILE, "r", encoding="utf-8") as f:
        replay_data = json.load(f)

    plot_convergence_comparison(r7_data, r8_data)
    plot_transition_dynamics(r8_data, replay_data)
    print("=== All Package 171 scientific figures successfully generated ===")


if __name__ == "__main__":
    main()
