# -*- coding: utf-8 -*-
"""
plot_f1705_candidate_e10_synthesis.py
======================================
Generates publication-quality 4-panel synthesis plot for Candidate E10 (Task F1705):
  Panel (a): Reaction force F(u_y) comparing Candidate E10 vs F1685 Combined Baseline.
  Panel (b): Stored elastic strain energy U and dissipated fracture energy D_f evolution.
  Panel (c): Mesh economy comparison (physical elements and active DOFs).
  Panel (d): Computational cost comparison (CPU time and walltime speedup).
"""
import re
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

repo_root = Path(__file__).resolve().parents[2]
e10_dir = repo_root / "models" / "pandey_kumar_mode1" / "177_method_a_hole_e10_prod"
f1685_dir = repo_root / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole"
results_dir = repo_root / "results" / "validation"
fig_dir_thesis = repo_root / "MA_AdaptiveRemeshing_Report_2026" / "figures"

# 1. Load Candidate E10 DAT
dat_e10 = e10_dir / "M1_HOLE_SEL_E10_PROD.dat"
u_e10, rf_e10 = [], []
with open(dat_e10, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()
pattern = re.compile(r'^\s*999999\s+([0-9.+-E]+)\s+([0-9.+-E]+)', re.MULTILINE)
for m in pattern.findall(text):
    u_e10.append(float(m[0]))
    rf_e10.append(float(m[1]))

# 2. Load F1685 Baseline DAT
dat_f1685 = f1685_dir / "M1_HOLE_F1685_COMBINED_PROD.dat"
u_f1685, rf_f1685 = [], []
if dat_f1685.exists():
    with open(dat_f1685, "r", encoding="utf-8", errors="replace") as f:
        text_f = f.read()
    for m in pattern.findall(text_f):
        u_f1685.append(float(m[0]))
        rf_f1685.append(float(m[1]))

# 3. Load Energy Balance CSVs
energy_e10 = e10_dir / "uel_energy_balance.csv"
u_eng_e10, U_e10, Df_e10, Etot_e10 = [], [], [], []
with open(energy_e10, "r", encoding="utf-8") as f:
    for line in f:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 7 and parts[0] != "step":
            try:
                st = int(parts[0])
                tt = float(parts[2])
                s_time = float(parts[3])
                disp = tt * 0.005 if st == 1 else 0.005 + s_time * 0.010
                u_eng_e10.append(disp)
                U_e10.append(float(parts[4]) * 1000.0) # J to mJ
                Df_e10.append(float(parts[5]) * 1000.0)
                Etot_e10.append(float(parts[6]) * 1000.0)
            except ValueError:
                pass

energy_f1685 = f1685_dir / "f1685_uel_energy_balance.csv"
u_eng_f1685, U_f1685, Df_f1685 = [], [], []
if energy_f1685.exists():
    with open(energy_f1685, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                try:
                    st = int(parts[0])
                    tt = float(parts[2])
                    s_time = float(parts[3])
                    disp = tt * 0.005 if st == 1 else 0.005 + s_time * 0.010
                    u_eng_f1685.append(disp)
                    U_f1685.append(float(parts[4]) * 1000.0)
                    Df_f1685.append(float(parts[5]) * 1000.0)
                except ValueError:
                    pass

plt.rcParams.update({
    "font.size": 10,
    "font.family": "serif",
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "figure.titlesize": 13,
    "lines.linewidth": 1.6
})

fig, axes = plt.subplots(2, 2, figsize=(11.5, 9.0), dpi=300)

# Panel (a): Load-Displacement F(u_y)
ax = axes[0, 0]
if u_f1685:
    ax.plot(np.array(u_f1685) * 1000.0, rf_f1685, label="F1685 Baseline (21,569 el, Job 1421171)", color="#1f77b4", linestyle="--", alpha=0.85)
ax.plot(np.array(u_e10) * 1000.0, rf_e10, label="Candidate E10 Selective (9,164 el, Job 1421888)", color="#d62728", linestyle="-")

ax.set_xlabel(r"Prescribed Displacement $u_y$ [$\mu$m]")
ax.set_ylabel(r"Reaction Force $F$ [kN]")
ax.set_title("(a) Load-Displacement Parity ($P(u_y)$)", fontweight="bold")
ax.grid(True, linestyle=":", alpha=0.6)
ax.set_xlim(0, 11)
ax.set_ylim(-0.02, 0.65)
ax.axvline(x=5.36, color="gray", linestyle=":", alpha=0.7)
ax.annotate(r"$P_{\max} = 0.5597$ kN (+0.36%)", xy=(5.36, 0.5597), xytext=(5.9, 0.58),
            arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1, headwidth=5), fontsize=8.5)
ax.legend(loc="upper right")

# Panel (b): Energy Evolution
ax = axes[0, 1]
ax.plot(np.array(u_eng_e10) * 1000.0, U_e10, label=r"Elastic Strain Energy $U$ (E10)", color="#2ca02c", linestyle="-")
ax.plot(np.array(u_eng_e10) * 1000.0, Df_e10, label=r"Dissipated Fracture Energy $D_f$ (E10)", color="#ff7f0e", linestyle="-")
if u_eng_f1685:
    ax.plot(np.array(u_eng_f1685) * 1000.0, U_f1685, label=r"Elastic $U$ (F1685 Baseline)", color="#2ca02c", linestyle=":", alpha=0.6)
    ax.plot(np.array(u_eng_f1685) * 1000.0, Df_f1685, label=r"Fracture $D_f$ (F1685 Baseline)", color="#ff7f0e", linestyle=":", alpha=0.6)

ax.set_xlabel(r"Prescribed Displacement $u_y$ [$\mu$m]")
ax.set_ylabel(r"Energy [mJ]")
ax.set_title("(b) Energy Dissipation Evolution ($U$ vs $D_f$)", fontweight="bold")
ax.grid(True, linestyle=":", alpha=0.6)
ax.set_xlim(0, 11)
ax.set_ylim(-0.1, 3.2)
ax.annotate("Primary Hole\nArrest Plateau", xy=(6.0, 0.46), xytext=(3.3, 0.9),
            arrowprops=dict(facecolor="#ff7f0e", shrink=0.08, width=1, headwidth=5), fontsize=8)
ax.annotate(r"Complete Right Severance" "\n" r"($U \to 7.26\,\mu$J, -99.6%)", xy=(7.8, 0.05), xytext=(7.1, 0.7),
            arrowprops=dict(facecolor="#2ca02c", shrink=0.08, width=1, headwidth=5), fontsize=8)
ax.legend(loc="center left")

# Panel (c): Mesh Economy
ax = axes[1, 0]
categories = ["Physical\nElements", "Layered\nElements", "Active\nDOFs"]
f1685_counts = [21569, 64707, 64746]
e10_counts = [9164, 27492, 27694]
x = np.arange(len(categories))
width = 0.35

rects1 = ax.bar(x - width/2, f1685_counts, width, label="F1685 Combined Baseline", color="#1f77b4", alpha=0.85)
rects2 = ax.bar(x + width/2, e10_counts, width, label="Candidate E10 Selective", color="#d62728", alpha=0.85)

ax.set_ylabel("Quantity Count")
ax.set_title("(c) Discretization Size Reduction", fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.grid(True, linestyle=":", alpha=0.6, axis="y")
ax.legend(loc="upper right")

for i in range(len(categories)):
    red = ((f1685_counts[i] - e10_counts[i]) / f1685_counts[i]) * 100.0
    ax.annotate(f"-{red:.1f}%", xy=(x[i] + width/2, e10_counts[i] + 1800), ha="center", fontsize=9, fontweight="bold", color="#d62728")

# Panel (d): Computational Cost Speedup
ax = axes[1, 1]
timing_cats = ["Solver CPU Time\n[minutes]", "Solver Walltime\n[minutes]"]
f1685_times = [3230.0 / 60.0, 4810.0 / 60.0]
e10_times = [1180.0 / 60.0, 1921.0 / 60.0]
x_t = np.arange(len(timing_cats))

rects_t1 = ax.bar(x_t - width/2, f1685_times, width, label="F1685 Combined Baseline", color="#1f77b4", alpha=0.85)
rects_t2 = ax.bar(x_t + width/2, e10_times, width, label="Candidate E10 Selective", color="#d62728", alpha=0.85)

ax.set_ylabel("Execution Time [minutes]")
ax.set_title("(d) Computational Efficiency & Speedup (2.74x)", fontweight="bold")
ax.set_xticks(x_t)
ax.set_xticklabels(timing_cats)
ax.grid(True, linestyle=":", alpha=0.6, axis="y")
ax.legend(loc="upper right")

for i in range(len(timing_cats)):
    red = ((f1685_times[i] - e10_times[i]) / f1685_times[i]) * 100.0
    speedup = f1685_times[i] / e10_times[i]
    ax.annotate(f"-{red:.1f}%\n({speedup:.2f}x speedup)", xy=(x_t[i] + width/2, e10_times[i] + 3), ha="center", fontsize=8.5, fontweight="bold", color="#d62728")

plt.tight_layout()

png_out = results_dir / "f1705_candidate_e10_synthesis.png"
pdf_out = fig_dir_thesis / "fig_f1705_candidate_e10_synthesis.pdf"

plt.savefig(png_out, dpi=300)
plt.savefig(pdf_out)
plt.close()

print(f"[PASS] Successfully generated synthesis plots:\n  PNG: {png_out}\n  PDF: {pdf_out}")
