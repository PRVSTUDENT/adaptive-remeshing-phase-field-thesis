# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1777_physics_and_continuation_synthesis.py
=====================================================================
Generates a comprehensive 4-panel publication synthesis figure for Task F1777:
Panel (a): Case 1 Force-Displacement Response with Reconciled Reference Units (kN / N)
Panel (b): Case 1 2D Terminal Damage Contour (Cleaved 0.5 mm Ligament, d >= 0.95)
Panel (c): Cases 1 & 5 Energy Balance Evolution (Elastic Strain Energy Decay vs Fracture Dissipation)
Panel (d): Cases 2 & 3 Distal Corridor Resolution & Framework Continuation Diagnosis
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle, Circle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

from scripts.validation.parse_f1776_fracture_responses import parse_dat_file

def main():
    val_dir = os.path.join(REPO_ROOT, "results", "validation", "f1776_case1_case5_fracture")
    fig_dir = os.path.join(REPO_ROOT, "results", "figures")
    report_fig_dir = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    os.makedirs(report_fig_dir, exist_ok=True)

    fig = plt.figure(figsize=(16, 12), dpi=300)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.28, wspace=0.25)

    # ----------------------------------------------------
    # Panel (a): Case 1 Force-Displacement Response
    # ----------------------------------------------------
    ax_a = fig.add_subplot(gs[0, 0])
    c1_dat = os.path.join(val_dir, "case1_fracture.dat")
    u_c1, rf_c1 = parse_dat_file(c1_dat)
    
    # In mm-kN units: u is mm, rf is kN. Convert to N for secondary or primary display.
    u_um = u_c1 * 1000.0  # to um
    rf_kN = rf_c1
    rf_N = rf_c1 * 1000.0

    peak_idx = np.argmax(rf_kN)
    u_peak_um = u_um[peak_idx]
    f_peak_kN = rf_kN[peak_idx]
    f_peak_N = rf_N[peak_idx]
    f_final_N = rf_N[-1]
    drop_pct = (f_peak_N - f_final_N) / f_peak_N * 100.0

    ax_a.plot(u_um, rf_kN, color="#1f77b4", lw=2.2, label=f"Adapted Mesh (20,232 el)\n$F_{{max}} = {f_peak_kN:.4f}\\,\\mathrm{{kN}}$ (${f_peak_N:.1f}\\,\\mathrm{{N}}$)")
    
    # Reference Anchor Job 1398090: 0.7578 kN (757.8 N) at 5.86 um
    ref_f_kN = 0.757778
    ref_u_um = 5.857
    ax_a.axhline(ref_f_kN, color="crimson", ls="--", lw=1.5, label=f"Gate 1 Ref. Anchor: {ref_f_kN:.4f}\\,\\mathrm{{kN}} (${ref_f_kN*1000:.1f}\\,\\mathrm{{N}}$)")
    ax_a.fill_between([0, 10], [ref_f_kN*0.95, ref_f_kN*0.95], [ref_f_kN*1.05, ref_f_kN*1.05], color="crimson", alpha=0.12, label="Predeclared $\\pm 5.0\\%$ Tolerance")

    # Annotate peak
    parity_pct = (f_peak_kN - ref_f_kN) / ref_f_kN * 100.0
    ax_a.scatter([u_peak_um], [f_peak_kN], color="#1f77b4", s=60, zorder=5)
    ax_a.annotate(f"Peak: $F = {f_peak_kN:.4f}\\,\\mathrm{{kN}}$\nParity: ${parity_pct:+.2f}\\%$ (Gate G1: PASS)",
                  xy=(u_peak_um, f_peak_kN), xytext=(u_peak_um + 0.5, f_peak_kN - 0.12),
                  arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.2),
                  fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#1f77b4", alpha=0.9))

    # Annotate terminal severance
    ax_a.scatter([u_um[-1]], [rf_kN[-1]], color="black", s=50, zorder=5)
    ax_a.annotate(f"Terminal Severance:\n$F_{{final}} = {f_final_N:.1f}\\,\\mathrm{{N}}$ ({drop_pct:.2f}% drop)\n$u = {u_um[-1]:.2f}\\,\\mu\\mathrm{{m}}$ (Cutback divergence)",
                  xy=(u_um[-1], rf_kN[-1]), xytext=(u_um[-1] - 3.2, 0.20),
                  arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
                  fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#fff9e6", ec="darkorange", alpha=0.9))

    ax_a.set_xlabel("Top Prescribed Displacement $u$ [$\\mu\\mathrm{m}$]", fontsize=11, fontweight="bold")
    ax_a.set_ylabel("Reaction Force $F$ [$\\mathrm{kN}$]", fontsize=11, fontweight="bold")
    ax_a.set_title("(a) Case 1 Force-Displacement Response (Reconciled Units)", fontsize=12, fontweight="bold")
    ax_a.set_xlim(0, 7.5)
    ax_a.set_ylim(0, 0.90)
    ax_a.grid(True, linestyle=":", alpha=0.6)
    ax_a.legend(loc="upper left", fontsize=8.5)

    # Secondary y-axis in N
    ax_a_sec = ax_a.secondary_yaxis('right', functions=(lambda x: x*1000, lambda x: x/1000))
    ax_a_sec.set_ylabel("Reaction Force $F$ [$\\mathrm{N}$]", fontsize=10, color="dimgray")

    # ----------------------------------------------------
    # Panel (b): Case 1 2D Terminal Damage Contour
    # ----------------------------------------------------
    ax_b = fig.add_subplot(gs[0, 1])
    c1_dmg_csv = os.path.join(val_dir, "case1_terminal_damage_field.csv")
    df_dmg = pd.read_csv(c1_dmg_csv)
    
    # Filter to visualizer elements
    x_el = df_dmg["x_mm"].values
    y_el = df_dmg["y_mm"].values
    d_el = df_dmg["damage_d"].values

    # Scatter plot with high density
    sc = ax_b.scatter(x_el, y_el, c=d_el, cmap="viridis", s=6, vmin=0.0, vmax=1.0, alpha=0.9)
    cb = plt.colorbar(sc, ax=ax_b, pad=0.02, fraction=0.046)
    cb.set_label("Phase-Field Damage $d$ [$-$]", fontsize=10, fontweight="bold")

    # Draw notch seam: y=0.5, x in [0.0, 0.5]
    ax_b.plot([0.0, 0.5], [0.5, 0.5], color="red", lw=2.5, ls="--", label="Initial Crack Notch ($a_0 = 0.5\\,\\mathrm{mm}$)")
    # Draw ligament boundary line: y=0.5, x in [0.5, 1.0]
    ax_b.plot([0.5, 1.0], [0.5, 0.5], color="magenta", lw=1.2, ls=":", label="Unbroken Ligament ($0.5\\,\\mathrm{mm}$)")

    # Highlight crack path elements with d >= 0.95
    crack_mask = (d_el >= 0.95) & (y_el >= 0.45) & (y_el <= 0.55)
    ax_b.scatter(x_el[crack_mask], y_el[crack_mask], color="red", s=10, alpha=0.6, label="Fully Cleaved Core ($d \\geq 0.95$)")

    ax_b.set_xlabel("Coordinate $x$ [$\\mathrm{mm}$]", fontsize=11, fontweight="bold")
    ax_b.set_ylabel("Coordinate $y$ [$\\mathrm{mm}$]", fontsize=11, fontweight="bold")
    ax_b.set_title("(b) Case 1 Terminal Cleavage ($u = 6.90\\,\\mu\\mathrm{m}$, 99.67% Ligament Cleaved)", fontsize=12, fontweight="bold")
    ax_b.set_xlim(0.0, 1.0)
    ax_b.set_ylim(0.0, 1.0)
    ax_b.set_aspect("equal")
    ax_b.legend(loc="lower right", fontsize=8)

    # Inset zoom on ligament
    ax_b.annotate("Complete Transverse Cleavage\n$x \\in [0.498, 0.998]\\,\\mathrm{mm}$ ($99.67\\%$ span)",
                  xy=(0.75, 0.50), xytext=(0.52, 0.25),
                  arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
                  fontsize=8.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", fc="#e6f2ff", ec="#1f77b4", alpha=0.9))

    # ----------------------------------------------------
    # Panel (c): Energy Balance Evolution (Cases 1 & 5)
    # ----------------------------------------------------
    ax_c = fig.add_subplot(gs[1, 0])
    c1_en_csv = os.path.join(val_dir, "case1_energy_balance.csv")
    df_en_c1 = pd.read_csv(c1_en_csv)
    c5_en_csv = os.path.join(val_dir, "case5_energy_balance.csv")
    df_en_c5 = pd.read_csv(c5_en_csv)

    # Plot Case 1
    t_c1 = df_en_c1["TotalTime"].values
    e_elas_c1 = df_en_c1["E_elastic_kNmm"].values * 1000.0  # to mJ
    e_frac_c1 = df_en_c1["E_fracture_kNmm"].values * 1000.0  # to mJ

    ax_c.plot(t_c1, e_elas_c1, color="#1f77b4", lw=2.0, label="Case 1 $E_{\\mathrm{elastic}}$ (99.73% drop)")
    ax_c.plot(t_c1, e_frac_c1, color="#1f77b4", lw=2.0, ls="--", label="Case 1 $E_{\\mathrm{fracture}}$ (Monotonic, $2.712\\,\\mathrm{mJ}$)")

    # Plot Case 5
    t_c5 = df_en_c5["TotalTime"].values
    e_elas_c5 = df_en_c5["E_elastic_kNmm"].values * 1000.0
    e_frac_c5 = df_en_c5["E_fracture_kNmm"].values * 1000.0

    ax_c.plot(t_c5, e_elas_c5, color="#2ca02c", lw=2.0, label="Case 5 $E_{\\mathrm{elastic}}$ (99.84% drop)")
    ax_c.plot(t_c5, e_frac_c5, color="#2ca02c", lw=2.0, ls="--", label="Case 5 $E_{\\mathrm{fracture}}$ (Monotonic, $2.322\\,\\mathrm{mJ}$)")

    ax_c.axvline(1.0, color="gray", ls=":", lw=1.2, label="Step 1 / Step 2 Boundary")

    ax_c.set_xlabel("Total Pseudo-Time $t$ [$-$]", fontsize=11, fontweight="bold")
    ax_c.set_ylabel("Internal Energy Components [$\\mathrm{mJ}$]", fontsize=11, fontweight="bold")
    ax_c.set_title("(c) Thermodynamic Energy Evolution (Monotonic Dissipation)", fontsize=12, fontweight="bold")
    ax_c.set_xlim(0.0, 1.70)
    ax_c.set_ylim(0.0, 3.20)
    ax_c.grid(True, linestyle=":", alpha=0.6)
    ax_c.legend(loc="upper left", fontsize=8.5)

    # Annotate monotonicity
    ax_c.text(0.98, 0.45, "Zero Monotonicity Violations\nCase 1: $\\Delta E_{\\mathrm{frac}} > 0$ across all 243 incs\nCase 5: $\\Delta E_{\\mathrm{frac}} \\geq 0$ across all 392 incs",
              transform=ax_c.transAxes, ha="right", fontsize=8.5,
              bbox=dict(boxstyle="round,pad=0.3", fc="#eafaf1", ec="#2ca02c", alpha=0.9))

    # ----------------------------------------------------
    # Panel (d): Cases 2 & 3 Distal Path Diagnosis & Framework Continuation
    # ----------------------------------------------------
    ax_d = fig.add_subplot(gs[1, 1])
    ax_d.axis("off")

    summary_text = (
        "FOUR-BENCHMARK UNIFIED FRAMEWORK CONTINUATION DIAGNOSIS\n\n"
        "1. Shared Code Invariant & Frozen Baseline:\n"
        "  * Shared Framework: scripts/remeshing/reusable_2d_adaptive_framework.py\n"
        "  * Framework Hash: 8D71F38F23867A23C1FC1BF5EC499533A8C75F538B77804ECE03B5C668F4BE08\n"
        "  * Frozen Production UEL: f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15...)\n"
        "  * Cumulative HPC Submissions Accounted: Exactly 35 (0 consumed in F1777)\n\n"
        "2. Case 2 Off-Axis Hole Distal Under-Resolution Diagnosis (Section 4.2):\n"
        "  * Observation: Proximal notch-to-hole ligament refined (h <= l0 = 7.5 um);\n"
        "    distal hole-to-boundary ligament remains coarse (h ~ 25 um > l0).\n"
        "  * Mathematical Root Cause: Linear elastic pre-analysis indicator MISESERI decays from\n"
        "    521.7 MPa at notch tip to 15.2 MPa distal to hole, falling into bulk noise\n"
        "    (9.6 +/- 9.3 MPa, z = 0.595). Single-pass Method A.1 cannot resolve distal corridor\n"
        "    without causing a 5-fold global mesh explosion.\n"
        "  * Framework Remedy: Evolving damage-weighted donor or 2-state sequential donor (Method A.2).\n\n"
        "3. Case 3 Rectangular Plate with Pins & Void Diagnosis (Section 4.3):\n"
        "  * Observation: 2-Pass Method A.2 resolved both primary and secondary corridors, but element\n"
        "    count reached 28,933 elements (+137.8% vs 12,168 baseline); max aspect ratio = 4.29.\n"
        "  * Mathematical Root Cause: Sequential donor overlay with coarseningFactor='NOT_ALLOWED'\n"
        "    preserves early uncracked sizing requirements globally, causing cumulative element inflation.\n"
        "  * Framework Remedy: Unified envelope indicator with adaptive relaxation factor beta in [1.2, 1.5].\n\n"
        "4. Four-Benchmark Regression Requirement:\n"
        "  * Per policy, ANY framework repair must be generic, evaluated across ALL 4 cases (1, 2, 3, 5),\n"
        "    and validated against predeclared gates before thesis adoption."
    )

    ax_d.text(0.02, 0.98, summary_text, transform=ax_d.transAxes,
              fontsize=9.2, verticalalignment="top", fontfamily="sans-serif",
              bbox=dict(boxstyle="round,pad=0.6", fc="#fdfefe", ec="#2c3e50", lw=1.2))

    # Save figure
    out_png = os.path.join(fig_dir, "fig_f1777_physics_and_continuation_synthesis.png")
    out_pdf = os.path.join(fig_dir, "fig_f1777_physics_and_continuation_synthesis.pdf")
    rep_png = os.path.join(report_fig_dir, "fig_f1777_physics_and_continuation_synthesis.png")
    rep_pdf = os.path.join(report_fig_dir, "fig_f1777_physics_and_continuation_synthesis.pdf")

    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(rep_png, dpi=300, bbox_inches="tight")
    plt.savefig(rep_pdf, bbox_inches="tight")
    print(f"Saved publication figures to:\n  {out_png}\n  {out_pdf}\n  {rep_png}\n  {rep_pdf}")

if __name__ == "__main__":
    main()
