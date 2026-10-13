#!/usr/bin/env python3
"""
Publication-Quality Visualization: Method C Gate C1 V2 State Transfer & Continuation
Task F1436: Mode-I Method C Gate C1 Evaluation
Protocol Version: 2

Generates:
1. Fig 1: Two-panel scientific comparison:
   (a) Global load-displacement response showing Step 1 reload, handoff continuity,
       and Step 2 continuation on the coarse recipient mesh vs donor and reference.
   (b) UEL energy balance evolution showing elastic and fracture energy components
       and seamless continuity across the step transition boundary.
Outputs saved to results/figures/mode1_method_c_gate_c1/ in PNG (300 DPI) and vector PDF.
"""

import os
import sys
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
EVIDENCE_C1_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "39_method_c_transfer_gate_c1" / "evidence_1412464"
C1_CSV = EVIDENCE_C1_DIR / "c1_load_displacement.csv"
C1_ENERGY_CSV = EVIDENCE_C1_DIR / "uel_energy_balance.csv"

HARVEST_DIR = REPO_ROOT / "runs" / "mode1" / "harvest_results_f1416"
NATIVE_14K_CSV = HARVEST_DIR / "m1_mb_native_14k_1s_load_displacement.csv"
ET2_6K_CSV = HARVEST_DIR / "m1_mb_et2_6k_1s_load_displacement.csv"
S1_REF_CSV = REPO_ROOT / "models" / "pandey_kumar_mode1" / "gate6b_claims_and_matched_audit" / "history_S1_1409734.mmaster02.csv"

OUT_DIR = REPO_ROOT / "results" / "figures" / "mode1_method_c_gate_c1"


def load_c1_fu(csv_path):
    s1_u, s1_f = [], []
    s2_u, s2_f = [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            step = int(r["step"])
            u = float(r["u2_mm"])
            rf = float(r["rf2_kn"])
            if step == 1:
                s1_u.append(u)
                s1_f.append(rf)
            else:
                s2_u.append(u)
                s2_f.append(rf)
    return np.array(s1_u), np.array(s1_f), np.array(s2_u), np.array(s2_f)


def load_c1_energy(csv_path):
    times, e_elas, e_frac, e_tot = [], [], [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            times.append(float(r["TotalTime"]))
            e_elas.append(float(r["E_elastic_kNmm"]) * 1000.0)  # kN*mm -> mJ
            e_frac.append(float(r["E_fracture_kNmm"]) * 1000.0)
            e_tot.append(float(r["E_total_kNmm"]) * 1000.0)
    return np.array(times), np.array(e_elas), np.array(e_frac), np.array(e_tot)


def load_generic_fu(csv_path, u_col="u_mm", f_col="f_kN"):
    if not csv_path.exists():
        return None, None
    u, f = [], []
    with open(csv_path, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for r in reader:
            if u_col in r and f_col in r:
                u.append(float(r[u_col]))
                f.append(float(r[f_col]))
            elif "u_prescribed_mm" in r and "reaction_force_kn" in r:
                u.append(float(r["u_prescribed_mm"]))
                f.append(float(r["reaction_force_kn"]))
    return np.array(u), np.array(f)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    s1_u, s1_f, s2_u, s2_f = load_c1_fu(C1_CSV)
    times, e_elas, e_frac, e_tot = load_c1_energy(C1_ENERGY_CSV)

    nat_u, nat_f = load_generic_fu(NATIVE_14K_CSV, "u_mm", "f_kN")
    s1_ref_u, s1_ref_f = load_generic_fu(S1_REF_CSV)

    # 2. Configure Matplotlib style for university publishing
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "legend.fontsize": 8.5,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "figure.titlesize": 12,
        "lines.linewidth": 1.5,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linestyle": ":",
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.0), dpi=300)

    # -------------------------------------------------------------
    # Panel (a): Load-Displacement Response
    # -------------------------------------------------------------
    if s1_ref_u is not None and len(s1_ref_u) > 0:
        ax1.plot(s1_ref_u, s1_ref_f, color="#444444", linestyle="--", linewidth=1.3,
                 label=r"Fixed Reference (15,192 FE, $F_{\max}=0.758$ kN)", alpha=0.75)

    if nat_u is not None and len(nat_u) > 0:
        ax1.plot(nat_u, nat_f, color="#D95F02", linestyle=":", linewidth=1.4,
                 label=r"Method B Donor Mesh (14,677 FE, $F_{\max}=0.743$ kN)", alpha=0.85)

    # Step 1 reload
    ax1.plot(s1_u, s1_f, color="#1B9E77", linewidth=2.0,
             label=r"Method C Step 1: Equilibrium Reload ($u \leq 0.005$ mm)")

    # Step 2 continuation
    ax1.plot(s2_u, s2_f, color="#7570B3", linewidth=2.0,
             label=r"Method C Step 2: Continuation on 2,906 FE ($F_{\max}=1.087$ kN)")

    # Mark handoff point
    handoff_u = s1_u[-1]
    handoff_f = s1_f[-1]
    ax1.scatter([handoff_u], [handoff_f], color="#E7298A", s=50, zorder=5,
                label=r"Handoff Boundary ($u=0.005$ mm, $\Delta F=0.09$ N)")

    # Annotate handoff
    ax1.annotate(
        "Handoff Continuity\n"
        r"$F_{\mathrm{handoff}} = 0.6525\ \mathrm{kN}$" "\n"
        r"$\Delta F = 0.0925\ \mathrm{N}$",
        xy=(handoff_u, handoff_f),
        xytext=(0.0018, 0.85),
        arrowprops=dict(facecolor="#E7298A", shrink=0.08, width=1.0, headwidth=5.0),
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF0F5", edgecolor="#E7298A", alpha=0.9)
    )

    # Annotate peak delay
    peak_idx = np.argmax(s2_f)
    peak_u = s2_u[peak_idx]
    peak_f = s2_f[peak_idx]
    ax1.annotate(
        "Coarse Mesh Delay\n"
        r"($h > l_0 \rightarrow F_{\max}=1.087\ \mathrm{kN}$)",
        xy=(peak_u, peak_f),
        xytext=(0.0058, 1.15),
        arrowprops=dict(facecolor="#7570B3", shrink=0.08, width=1.0, headwidth=5.0),
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#F0F0FF", edgecolor="#7570B3", alpha=0.9)
    )

    ax1.set_xlabel(r"Prescribed Displacement $u_y$ [mm]")
    ax1.set_ylabel(r"Total Reaction Force $F_y$ [kN]")
    ax1.set_title("(a) Load-Displacement Response & Handoff Continuity", fontweight="bold", pad=8)
    ax1.set_xlim(0.0, 0.0105)
    ax1.set_ylim(-0.02, 1.25)
    ax1.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax1.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax1.legend(loc="upper left", framealpha=0.92)

    # -------------------------------------------------------------
    # Panel (b): Global UEL Energy Evolution
    # -------------------------------------------------------------
    ax2.plot(times, e_tot, color="#2B83BA", linewidth=2.0, label=r"Total Energy $E_{\mathrm{tot}} = E_{\mathrm{elas}} + E_{\mathrm{frac}}$")
    ax2.plot(times, e_elas, color="#D7191C", linewidth=1.8, linestyle="--", label=r"Stored Elastic Strain Energy $E_{\mathrm{elas}}$")
    ax2.plot(times, e_frac, color="#FDAE61", linewidth=1.8, linestyle="-.", label=r"Dissipated Fracture Energy $E_{\mathrm{frac}}$")

    # Step transition line at t = 1.0
    ax2.axvline(1.0, color="#666666", linestyle=":", linewidth=1.2)
    ax2.text(0.50, 4.5, "Step 1: Reload\n(Elastic Domain)", ha="center", va="center", fontsize=8.5,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#EEEEEE", edgecolor="#888888", alpha=0.85))
    ax2.text(1.50, 4.5, "Step 2: Continuation\n(Fracture Domain)", ha="center", va="center", fontsize=8.5,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#EEEEEE", edgecolor="#888888", alpha=0.85))

    # Mark snap-through conversion
    ax2.annotate(
        "Fracture Snap-Through\n"
        r"$E_{\mathrm{elas}} \rightarrow E_{\mathrm{frac}}$ transition" "\n"
        "(14 adaptive cutbacks)",
        xy=(1.94, 0.95),
        xytext=(1.20, 2.5),
        arrowprops=dict(facecolor="#D7191C", shrink=0.08, width=1.0, headwidth=5.0),
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF8DC", edgecolor="#D7191C", alpha=0.9)
    )

    ax2.set_xlabel(r"Total Pseudo-Time $t_{\mathrm{total}}$ [-] (Step 1: $0\rightarrow 1$, Step 2: $1\rightarrow 2$)")
    ax2.set_ylabel(r"Global Energy Measures [mJ]")
    ax2.set_title("(b) Global UEL Energetic Partition & Dissipation", fontweight="bold", pad=8)
    ax2.set_xlim(0.0, 2.05)
    ax2.set_ylim(-0.1, 5.5)
    ax2.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax2.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax2.legend(loc="upper left", framealpha=0.92)

    plt.tight_layout()

    out_png = OUT_DIR / "fig_mode1_method_c_gate_c1_fu_and_energy.png"
    out_pdf = OUT_DIR / "fig_mode1_method_c_gate_c1_fu_and_energy.pdf"

    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()

    print(f"Generated publication figure pairs:")
    print(f"  PNG: {out_png} (size: {out_png.stat().st_size} bytes)")
    print(f"  PDF: {out_pdf} (size: {out_pdf.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
