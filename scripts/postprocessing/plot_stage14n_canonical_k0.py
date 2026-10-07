#!/usr/bin/env python3
"""Regenerate the canonical Mode-I K0 comparison with current job provenance."""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_dat_file(dat_path):
    """Extract reference-point displacement and reaction force from Abaqus .dat."""
    records = []
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as stream:
        for line in stream:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0] == "999999":
                try:
                    records.append({"u": float(parts[1]), "force": float(parts[2])})
                except ValueError:
                    pass
    return pd.DataFrame(records)


def generate_plot(base_dir=None, output_dir=None):
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if output_dir is None:
        output_dir = os.path.join(base_dir, "results", "figures", "mode1_gate6b")
    os.makedirs(output_dir, exist_ok=True)

    ref_path = os.path.join(
        base_dir,
        "models", "pandey_kumar_mode1", "gate6b_claims_and_matched_audit",
        "history_T2_1409734.mmaster02.csv",
    )
    et1_path = os.path.join(
        base_dir,
        "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
        "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv",
    )
    fine_path = os.path.join(
        base_dir,
        "models", "pandey_kumar_mode1", "37_stage14_adaptive_candidate_spatial_fine_8thread",
        "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_8T.dat",
    )

    ref = pd.read_csv(ref_path).rename(columns={"u_mm": "u", "force_kN": "force"})
    et1 = pd.read_csv(et1_path).rename(
        columns={"displacement_mm": "u", "reaction_force_kN": "force"}
    )
    fine = parse_dat_file(fine_path)

    u_min = 0.5 * 2.5e-6
    u_max = 0.0010 + 0.5 * 2.5e-6
    ref_fit = ref[(ref["u"] > u_min) & (ref["u"] <= u_max)].copy()
    et1_fit = et1[(et1["u"] > u_min) & (et1["u"] <= u_max)].copy()
    fine_fit = fine[(fine["u"] > u_min) & (fine["u"] <= u_max)].copy()
    if len(ref_fit) != 400 or len(et1_fit) != 400 or len(fine_fit) != 400:
        raise RuntimeError(
            "Canonical K0 window must contain 400 points: "
            f"ref={len(ref_fit)}, ET1={len(et1_fit)}, fine={len(fine_fit)}"
        )

    k_ref, b_ref = np.polyfit(ref_fit["u"], ref_fit["force"], 1)
    k_et1, b_et1 = np.polyfit(et1_fit["u"], et1_fit["force"], 1)
    k_fine, b_fine = np.polyfit(fine_fit["u"], fine_fit["force"], 1)
    et1_pred = k_et1 * et1_fit["u"] + b_et1
    fine_pred = k_fine * fine_fit["u"] + b_fine
    ss_res = float(np.sum((et1_fit["force"] - et1_pred) ** 2))
    ss_tot = float(np.sum((et1_fit["force"] - et1_fit["force"].mean()) ** 2))
    r2_et1 = 1.0 - ss_res / ss_tot
    ss_res_fine = float(np.sum((fine_fit["force"] - fine_pred) ** 2))
    ss_tot_fine = float(np.sum((fine_fit["force"] - fine_fit["force"].mean()) ** 2))
    r2_fine = 1.0 - ss_res_fine / ss_tot_fine
    rel_diff = (k_et1 - k_ref) / k_ref * 100.0
    rel_diff_fine = (k_fine - k_ref) / k_ref * 100.0

    common_u = et1_fit["u"].to_numpy()
    ref_force = np.interp(common_u, ref_fit["u"], ref_fit["force"])
    rel_pointwise = (et1_fit["force"].to_numpy() - ref_force) / ref_force * 100.0
    fine_force = np.interp(common_u, fine_fit["u"], fine_fit["force"])
    rel_pointwise_fine = (fine_force - ref_force) / ref_force * 100.0

    fig, (ax, ax_diff) = plt.subplots(
        2, 1, figsize=(10.5, 9.0), dpi=300,
        gridspec_kw={"height_ratios": [3.0, 1.3], "hspace": 0.08},
    )
    ax.plot(ref_fit["u"] * 1000.0, ref_fit["force"], color="black", lw=2.2,
            label=f"Fixed Benchmark Anchor 15k (Job 1409734, K0={k_ref:.3f} kN/mm)")
    ax.plot(et1_fit["u"] * 1000.0, et1_fit["force"], color="blue", lw=1.8, ls="--",
            label=f"Corrected Adaptive ET1 14k (Job 1409982, K0={k_et1:.3f} kN/mm)")
    ax.plot(fine_fit["u"] * 1000.0, fine_fit["force"], color="#d62728", lw=1.6, ls=":",
            label=f"Spatial-Fine Adaptive Ref 58k (Job 1410504, K0={k_fine:.3f} kN/mm)")
    ax.set_title("Mode-I Initial Elastic Branch & Canonical K0 Fitting (u <= 1.0 um = 0.0010 mm)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Reaction Force F = -RF2 [kN]", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.55)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.tick_params(labelbottom=False)

    summary = (
        "Canonical K0 Qualification Summary\n"
        "Horizon: u in (0.00125, 1.00125] um (N=400)\n"
        f"Benchmark K0: {k_ref:.6f} kN/mm\n"
        f"Adaptive ET1 K0: {k_et1:.6f} kN/mm\n"
        f"Rel. Delta K0 (ET1 vs Bench): {rel_diff:+.4f}% (STABLE)\n"
        f"Spatial-Fine K0: {k_fine:.6f} kN/mm ({rel_diff_fine:+.4f}% vs Bench)\n"
        f"OLS R^2: ET1={r2_et1:.8f}; fine={r2_fine:.8f}\n"
        f"Adapt F(1.0 um): {et1_fit['force'].iloc[-1]:.6f} kN\n"
        f"Mean Pointwise Diff: ET1={np.mean(rel_pointwise):+.4f}%; fine={np.mean(rel_pointwise_fine):+.4f}%\n"
        "Unit Rule: 1 mm = 1000 um, delta_u = 0.0025 um"
    )
    ax.text(0.48, 0.09, summary, transform=ax.transAxes, fontsize=9.2,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#fff2cc", edgecolor="#8c7a54"))

    ax_diff.plot(common_u * 1000.0, rel_pointwise, color="green", lw=1.4, marker=".", ms=2.2,
                 label="ET1 relative difference [%]")
    ax_diff.plot(common_u * 1000.0, rel_pointwise_fine, color="#d62728", lw=1.2, ls=":",
                 label="Spatial-fine relative difference [%]")
    ax_diff.axhline(0.0, color="gray", lw=0.9, ls="--")
    ax_diff.set_xlabel("Prescribed Top-Edge Displacement u [um] (where 1.0 um = 0.0010 mm)", fontsize=11)
    ax_diff.set_ylabel("Diff [%]", fontsize=10)
    ax_diff.set_ylim(-0.10, 0.10)
    ax_diff.grid(True, linestyle=":", alpha=0.55)
    ax_diff.legend(loc="lower right", fontsize=8.5)

    pdf_path = os.path.join(output_dir, "fig_mode1_stage14n_canonical_k0_fitting.pdf")
    png_path = os.path.join(output_dir, "fig_mode1_stage14n_canonical_k0_fitting.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return pdf_path, png_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    outputs = generate_plot(args.base_dir, args.output_dir)
    print("Generated:\n  " + "\n  ".join(outputs))
