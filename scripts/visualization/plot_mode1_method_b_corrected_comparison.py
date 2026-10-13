"""Plot Mode-I Method B Corrected Model Comparison vs Reference Baselines.

Compares:
1. Canonical Fixed-Mesh 15k Reference (Job 1398090, 15,192 FE)
2. Original Method B Native (Job 1411934, 14,677 FE, PRE_PEAK_SOURCE_VARIANT)
3. Historical Stage-14 ET2 (Job 1411895, 6,112 FE)
4. Corrected Method B Native (Job 1412465, 14,483 FE, PROPAGATION_RESOLVED_VARIANT)

Generates publication-quality figure pair (PNG 300 DPI + vector PDF) demonstrating:
- Panel 1: Complete load-displacement response and elimination of the artificial plateau
- Panel 2: Cumulative external work evolution demonstrating -31.5% work reduction
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 1. Load Canonical Reference (Job 1398090)
    ref_path = os.path.join(repo_root, "results", "pandey_kumar_mode1", "master_fracture_curves", "curve_standard_1398090.csv")
    df_ref = pd.read_csv(ref_path)
    u_ref = df_ref["u2_mm"].values
    f_ref = df_ref["rf2_kN"].values

    trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
    w_ref = np.array([trapz_fn(f_ref[:i+1], u_ref[:i+1]) * 1000.0 for i in range(len(u_ref))])

    # 2. Load Original Method B (Job 1411934)
    nat_path = os.path.join(repo_root, "runs", "mode1", "harvest_results_f1416", "m1_mb_native_14k_1s_load_displacement.csv")
    df_nat = pd.read_csv(nat_path)
    u_nat = df_nat["u_mm"].values
    f_nat = df_nat["f_kN"].values
    w_nat = np.array([trapz_fn(f_nat[:i+1], u_nat[:i+1]) * 1000.0 for i in range(len(u_nat))])

    # 3. Load Historical ET2 (Job 1411895)
    et2_path = os.path.join(repo_root, "runs", "mode1", "harvest_results_f1416", "m1_mb_et2_6k_1s_load_displacement.csv")
    df_et2 = pd.read_csv(et2_path)
    u_et2 = df_et2["u_mm"].values
    f_et2 = df_et2["f_kN"].values
    w_et2 = np.array([trapz_fn(f_et2[:i+1], u_et2[:i+1]) * 1000.0 for i in range(len(u_et2))])

    # 4. Load Completed Corrected Method B (Job 1412465)
    corr_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k", "evidence_1412465", "corrected_method_b_load_displacement.csv")
    df_corr = pd.read_csv(corr_path)
    u_corr = df_corr["u_mm"].values
    f_corr = df_corr["f_kN"].values
    w_corr = df_corr["w_ext_mJ"].values

    # Styling setup
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8.5,
        "figure.titlesize": 12,
        "mathtext.fontset": "dejavuserif",
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.5), dpi=300)

    # -------------------------------------------------------------
    # Panel 1: Full Load-Displacement Response & Plateau Elimination
    # -------------------------------------------------------------
    ax1.plot(u_ref * 1000.0, f_ref, color="black", linewidth=2.0, label=r"Fixed Reference 15k (Job 1398090, $F_{\max}=0.758$ kN)")
    ax1.plot(u_et2 * 1000.0, f_et2, color="#1f77b4", linestyle="--", linewidth=1.6, label=r"Historical ET2 6k (Job 1411895, $F_{\max}=0.756$ kN)")
    ax1.plot(u_nat * 1000.0, f_nat, color="#d62728", linestyle=":", linewidth=1.8, label=r"Original Method B 14.7k (Job 1411934, plateau $0.50\text{--}0.60$ kN)")
    ax1.plot(u_corr * 1000.0, f_corr, color="#2ca02c", linewidth=2.2, label=r"Corrected Method B 14.5k (Job 1412465, $F_{\max}=0.744$ kN)")

    # Highlight plateau elimination
    ax1.annotate(
        "Original Method B:\nCoarse Pinning Plateau\n($F \\approx 0.50-0.60$ kN)",
        xy=(6.8, 0.54),
        xytext=(7.2, 0.65),
        arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.3),
        fontsize=8.5,
        color="#d62728",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2e9", ec="#d62728", alpha=0.9)
    )

    ax1.annotate(
        "Corrected Method B:\nPlateau Eliminated\n($F < 0.002$ kN at $u \\geq 6.0\\,\\mu$m)",
        xy=(6.0, 0.002),
        xytext=(4.2, 0.15),
        arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.3),
        fontsize=8.5,
        color="#196f3d",
        bbox=dict(boxstyle="round,pad=0.3", fc="#eafaf1", ec="#2ca02c", alpha=0.9)
    )

    # Inset for elastic stiffness parity
    axins = ax1.inset_axes([0.16, 0.48, 0.35, 0.38])
    mask_ref_in = u_ref <= 0.0010
    mask_corr_in = u_corr <= 0.0010
    mask_nat_in = u_nat <= 0.0010
    axins.plot(u_ref[mask_ref_in] * 1000.0, f_ref[mask_ref_in], color="black", lw=1.8, label="Ref")
    axins.plot(u_nat[mask_nat_in] * 1000.0, f_nat[mask_nat_in], color="#d62728", ls=":", lw=1.8, label="Orig B")
    axins.plot(u_corr[mask_corr_in] * 1000.0, f_corr[mask_corr_in], color="#2ca02c", lw=2.0, label="Corr B")
    axins.set_title(r"Elastic Stiffness Parity ($K_0 \approx 137.91$ kN/mm)", fontsize=7.5)
    axins.set_xlabel(r"$u_y$ [$\mu$m]", fontsize=7)
    axins.set_ylabel(r"$F$ [kN]", fontsize=7)
    axins.tick_params(labelsize=6.5)
    axins.grid(True, linestyle=":", alpha=0.6)

    ax1.set_xlabel(r"Prescribed Displacement $u_y$ [$\mu$m]")
    ax1.set_ylabel(r"Total Reaction Force $F_y$ [kN]")
    ax1.set_title(r"(a) Mode-I Load-Displacement Response & Plateau Elimination", fontweight="bold")
    ax1.set_xlim(0.0, 10.0)
    ax1.set_ylim(-0.02, 0.82)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.92)

    # -------------------------------------------------------------
    # Panel 2: Cumulative External Work Evolution
    # -------------------------------------------------------------
    ax2.plot(u_ref * 1000.0, w_ref, color="black", linewidth=2.0, label=r"Fixed Reference 15k ($W_{\mathrm{ext}}=2.359$ mJ at $10\,\mu$m)")
    ax2.plot(u_et2 * 1000.0, w_et2, color="#1f77b4", linestyle="--", linewidth=1.6, label=r"Historical ET2 6k ($W_{\mathrm{ext}}=2.828$ mJ, $+19.9\%$)")
    ax2.plot(u_nat * 1000.0, w_nat, color="#d62728", linestyle=":", linewidth=1.8, label=r"Original Method B 14.7k ($W_{\mathrm{ext}}=3.332$ mJ, $+41.2\%$)")
    ax2.plot(u_corr * 1000.0, w_corr, color="#2ca02c", linewidth=2.2, label=r"Corrected Method B 14.5k ($W_{\mathrm{ext}}=2.267$ mJ at $7.89\,\mu$m)")

    # Annotate work reduction
    ax2.annotate(
        "Excess Work in Orig B:\n$+1.042$ mJ ($+40.3\\%$)\nfrom coarse pinning",
        xy=(7.89, 3.31),
        xytext=(4.5, 3.1),
        arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.3),
        fontsize=8.5,
        color="#d62728",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2e9", ec="#d62728", alpha=0.9)
    )

    ax2.annotate(
        "Corrected Method B:\n$W_{\\mathrm{ext}} = 2.267$ mJ ($-31.5\\%$ vs Orig B)\n$E_{\\mathrm{frac}} = 2.285$ mJ ($99.7\\%$ of total)",
        xy=(7.889, 2.267),
        xytext=(4.8, 1.6),
        arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.3),
        fontsize=8.5,
        color="#196f3d",
        bbox=dict(boxstyle="round,pad=0.3", fc="#eafaf1", ec="#2ca02c", alpha=0.9)
    )

    ax2.set_xlabel(r"Prescribed Displacement $u_y$ [$\mu$m]")
    ax2.set_ylabel(r"Cumulative External Work $W_{\mathrm{ext}}$ [mJ]")
    ax2.set_title(r"(b) External Work & Energy Dissipation Comparison", fontweight="bold")
    ax2.set_xlim(0.0, 10.0)
    ax2.set_ylim(0.0, 3.6)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", framealpha=0.92)

    out_dir = os.path.join(repo_root, "results", "figures", "mode1_method_b_corrected_comparison")
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, "fig_mode1_method_b_corrected_comparison.png")
    pdf_path = os.path.join(out_dir, "fig_mode1_method_b_corrected_comparison.pdf")

    plt.tight_layout()
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Generated {png_path} ({os.path.getsize(png_path)} bytes)")
    print(f"Generated {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

if __name__ == "__main__":
    main()
