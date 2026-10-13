"""Plot Mode-I Ligament Damage Profiles: Reference vs Original B vs Corrected B.

Directly compares the horizontal phase-field damage distribution d(x, y=0.5 mm)
and crack front propagation x_front(u) across:
1. Canonical Fixed-Mesh 15k Reference (Job 1398090, 15,192 FE)
2. Original Method B Native (Job 1411934, 14,677 FE, coarse far ligament pinning crack)
3. Corrected Method B Native (Job 1412465, 14,483 FE, fully refined corridor)

Demonstrates the physical mechanism of plateau elimination:
- In Original Method B, coarse elements pin the crack front at x ~ 0.61 - 0.72 mm across u in [0.0060, 0.0075] mm.
- In Corrected Method B, the refined corridor (h <= l0/2) allows complete snap-through to x ~ 1.0 mm by u = 0.0060 mm,
  matching the Canonical Reference.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # 1. Load Reference Ligament Profiles
    ref_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "16_energy_qualification_reference_15k", "mode1_reference_ligament_profiles.csv")
    df_ref = pd.read_csv(ref_path)

    # 2. Load Original Method B Ligament Profiles
    orig_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_14K_ligament_profiles.csv")
    df_orig = pd.read_csv(orig_path)

    # 3. Load Corrected Method B Ligament Profiles
    corr_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k", "evidence_1412465", "corrected_method_b_ligament_damage_profiles.csv")
    df_corr = pd.read_csv(corr_path)

    # 4. Load Corrected Matched States Summary
    states_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k", "evidence_1412465", "corrected_method_b_damage_matched_states.json")
    with open(states_path, "r") as f:
        corr_states = json.load(f)

    # Style configuration
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10.5,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8.5,
        "figure.titlesize": 12,
        "mathtext.fontset": "dejavuserif",
    })

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13.5, 9.5), dpi=300)

    # Filter centerline points (|y - 0.5| < 0.006 mm)
    def get_centerline(df, u_val, u_col="target_u_mm", x_col="x_coord", y_col="y_coord", d_col="damage_d"):
        sub = df[np.isclose(df[u_col].astype(float), u_val, atol=1e-5)]
        sub_center = sub[np.abs(sub[y_col].astype(float) - 0.5) < 0.006].copy()
        sub_center.sort_values(by=x_col, inplace=True)
        return sub_center[x_col].values, sub_center[d_col].values

    # -------------------------------------------------------------
    # Panel 1: Initiation State near Peak Load (u ~ 0.005857 mm)
    # -------------------------------------------------------------
    x_ref_pk, d_ref_pk = get_centerline(df_ref, 0.005857, "u_target_mm", "x_mm", "y_mm", "d")
    x_orig_pk, d_orig_pk = get_centerline(df_orig, 0.005857, "target_u_mm", "x_coord", "y_coord", "damage_d")
    x_corr_pk, d_corr_pk = get_centerline(df_corr, 0.005857, "target_u_mm", "x_coord", "y_coord", "damage_d_max")

    ax1.plot(x_ref_pk, d_ref_pk, color="black", lw=2.0, label="Fixed Reference 15k")
    ax1.plot(x_orig_pk, d_orig_pk, color="#d62728", ls=":", lw=1.8, label="Original Method B 14.7k")
    ax1.plot(x_corr_pk, d_corr_pk, color="#2ca02c", lw=2.0, label="Corrected Method B 14.5k")
    ax1.axhline(0.95, color="gray", ls="--", lw=0.9, alpha=0.7, label=r"Crack threshold $d=0.95$")
    ax1.set_xlabel(r"Ligament Coordinate $x$ [mm]")
    ax1.set_ylabel(r"Phase-Field Damage $d$")
    ax1.set_title(r"(a) Peak Load State ($u_y = 0.005857$ mm)", fontweight="bold")
    ax1.set_xlim(0.48, 1.01)
    ax1.set_ylim(-0.02, 1.05)
    ax1.grid(True, ls=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.92)

    # -------------------------------------------------------------
    # Panel 2: Immediate Post-Peak Snap-Through (u = 0.006000 mm)
    # -------------------------------------------------------------
    x_ref_06, d_ref_06 = get_centerline(df_ref, 0.0060, "u_target_mm", "x_mm", "y_mm", "d")
    x_orig_06, d_orig_06 = get_centerline(df_orig, 0.0060, "target_u_mm", "x_coord", "y_coord", "damage_d")
    x_corr_06, d_corr_06 = get_centerline(df_corr, 0.0060, "target_u_mm", "x_coord", "y_coord", "damage_d_max")

    ax2.plot(x_ref_06, d_ref_06, color="black", lw=2.0, label="Fixed Reference 15k (Severed)")
    ax2.plot(x_orig_06, d_orig_06, color="#d62728", ls=":", lw=1.8, label="Original Method B (Pinned at $x=0.61$ mm)")
    ax2.plot(x_corr_06, d_corr_06, color="#2ca02c", lw=2.0, label="Corrected Method B (Severed to $x=1.0$ mm)")
    ax2.axhline(0.95, color="gray", ls="--", lw=0.9, alpha=0.7)

    ax2.annotate(
        "Original B: Pinned at $x=0.61$ mm\nDue to coarse elements ($h > l_0$)",
        xy=(0.612, 0.95),
        xytext=(0.65, 0.65),
        arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.3),
        fontsize=8.5,
        color="#d62728",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2e9", ec="#d62728", alpha=0.9)
    )

    ax2.annotate(
        "Corrected B: Complete Snap-Through\n$x_{\\mathrm{front}} = 0.999$ mm ($100\\%$ severed)",
        xy=(0.999, 1.0),
        xytext=(0.65, 0.35),
        arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.3),
        fontsize=8.5,
        color="#196f3d",
        bbox=dict(boxstyle="round,pad=0.3", fc="#eafaf1", ec="#2ca02c", alpha=0.9)
    )

    ax2.set_xlabel(r"Ligament Coordinate $x$ [mm]")
    ax2.set_ylabel(r"Phase-Field Damage $d$")
    ax2.set_title(r"(b) Immediate Post-Peak ($u_y = 0.006000$ mm)", fontweight="bold")
    ax2.set_xlim(0.48, 1.01)
    ax2.set_ylim(-0.02, 1.05)
    ax2.grid(True, ls=":", alpha=0.6)
    ax2.legend(loc="lower left", framealpha=0.92)

    # -------------------------------------------------------------
    # Panel 3: Mid-Plateau Horizon (u = 0.007000 mm)
    # -------------------------------------------------------------
    x_ref_07, d_ref_07 = get_centerline(df_ref, 0.0070, "u_target_mm", "x_mm", "y_mm", "d")
    x_orig_07, d_orig_07 = get_centerline(df_orig, 0.0070, "target_u_mm", "x_coord", "y_coord", "damage_d")
    x_corr_07, d_corr_07 = get_centerline(df_corr, 0.0070, "target_u_mm", "x_coord", "y_coord", "damage_d_max")

    ax3.plot(x_ref_07, d_ref_07, color="black", lw=2.0, label="Fixed Reference 15k")
    ax3.plot(x_orig_07, d_orig_07, color="#d62728", ls=":", lw=1.8, label="Original Method B (Slow creep $x=0.70$ mm)")
    ax3.plot(x_corr_07, d_corr_07, color="#2ca02c", lw=2.0, label="Corrected Method B (Fully fractured)")
    ax3.axhline(0.95, color="gray", ls="--", lw=0.9, alpha=0.7)

    ax3.annotate(
        "Original B: Sustained Plateau ($F=0.525$ kN)\nCrack pinned; slow creep to $x=0.70$ mm",
        xy=(0.698, 0.95),
        xytext=(0.60, 0.65),
        arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.3),
        fontsize=8.5,
        color="#d62728",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2e9", ec="#d62728", alpha=0.9)
    )

    ax3.set_xlabel(r"Ligament Coordinate $x$ [mm]")
    ax3.set_ylabel(r"Phase-Field Damage $d$")
    ax3.set_title(r"(c) Plateau Horizon ($u_y = 0.007000$ mm)", fontweight="bold")
    ax3.set_xlim(0.48, 1.01)
    ax3.set_ylim(-0.02, 1.05)
    ax3.grid(True, ls=":", alpha=0.6)
    ax3.legend(loc="lower left", framealpha=0.92)

    # -------------------------------------------------------------
    # Panel 4: Crack Front Evolution x_front(u) vs Prescribed Displacement
    # -------------------------------------------------------------
    ref_u_evo = [0.001, 0.003, 0.005, 0.005857, 0.006, 0.0065, 0.007, 0.008, 0.010]
    ref_x_evo = [0.500, 0.500, 0.500, 0.500,    0.9985, 0.9985, 0.9985, 0.9985, 0.9985]

    orig_u_evo = [0.001, 0.002, 0.003, 0.005, 0.005727, 0.005857, 0.006, 0.0065, 0.007, 0.0075, 0.008, 0.010]
    orig_x_evo = [0.500, 0.500, 0.500, 0.500, 0.500,    0.6123,   0.6123, 0.6459, 0.6978, 0.7194, 0.9916, 0.9916]

    corr_u_evo = [st["actual_u_mm"] for st in corr_states]
    corr_x_evo = [st["crack_front_x_d95_mm"] for st in corr_states]

    ax4.plot(np.array(ref_u_evo) * 1000.0, ref_x_evo, color="black", marker="o", lw=2.0, label="Fixed Reference 15k")
    ax4.plot(np.array(orig_u_evo) * 1000.0, orig_x_evo, color="#d62728", marker="s", ls=":", lw=1.8, label="Original Method B 14.7k")
    ax4.plot(np.array(corr_u_evo) * 1000.0, corr_x_evo, color="#2ca02c", marker="^", lw=2.2, label="Corrected Method B 14.5k")

    ax4.axhline(1.0, color="gray", ls="--", lw=0.9, alpha=0.7, label=r"Plate Boundary ($x = 1.0$ mm)")

    ax4.annotate(
        "Plateau Range:\nCrack pinned in\ncoarse elements",
        xy=(6.5, 0.65),
        xytext=(4.0, 0.75),
        arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.3),
        fontsize=8.5,
        color="#d62728",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2e9", ec="#d62728", alpha=0.9)
    )

    ax4.annotate(
        "Refined Corridor:\nImmediate propagation\nto specimen edge",
        xy=(6.0, 0.999),
        xytext=(6.5, 0.40),
        arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.3),
        fontsize=8.5,
        color="#196f3d",
        bbox=dict(boxstyle="round,pad=0.3", fc="#eafaf1", ec="#2ca02c", alpha=0.9)
    )

    ax4.set_xlabel(r"Prescribed Displacement $u_y$ [$\mu$m]")
    ax4.set_ylabel(r"Crack Front Position $x_{\mathrm{front}}(d \geq 0.95)$ [mm]")
    ax4.set_title(r"(d) Crack Front Progression Across Loading History", fontweight="bold")
    ax4.set_xlim(0.0, 10.0)
    ax4.set_ylim(0.48, 1.03)
    ax4.grid(True, ls=":", alpha=0.6)
    ax4.legend(loc="lower right", framealpha=0.92)

    out_dir = os.path.join(repo_root, "results", "figures", "mode1_method_b_corrected_comparison")
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, "fig_mode1_method_b_ligament_profiles.png")
    pdf_path = os.path.join(out_dir, "fig_mode1_method_b_ligament_profiles.pdf")

    plt.tight_layout()
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Generated {png_path} ({os.path.getsize(png_path)} bytes)")
    print(f"Generated {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

if __name__ == "__main__":
    main()
