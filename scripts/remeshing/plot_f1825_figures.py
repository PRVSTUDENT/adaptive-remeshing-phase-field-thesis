#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generates publication figures for Task F1825:
fig_f1825_coarsening_metric_diagnosis.png and .pdf
"""

import os
import sys
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
summary_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "269_f1825_coarsening_diagnosis", "coarsening_metric_diagnosis_summary.json")

with open(summary_path, "r") as f:
    data = json.load(f)

cases = ["case_1", "case_2", "case_3", "case_5"]
case_labels = ["Case 1\n(Sec. 4.1)", "Case 2\n(Sec. 4.4)", "Case 3\n(Sec. 4.3)", "Case 5\n(Sec. 4.5)"]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# -------------------------------------------------------------
# Panel (a): Coarsening Ratio Comparison across Metric Definitions
# -------------------------------------------------------------
ax = axes[0, 0]
x = np.arange(len(cases))
w = 0.25

base_ratios = [data[c]["baseline_audit"]["refinement_ratio"] for c in cases]
size_ratios = [data[c]["size_thresholded_partitioning"]["refinement_ratio"] for c in cases]
corner_ratios = [data[c]["geometric_corner_far_field"]["ratio_corner_mean_to_min"] for c in cases]

rects1 = ax.bar(x - w, base_ratios, w, label="Baseline Audit (Inconsistent Adapter)", color="#d9534f", alpha=0.85, edgecolor='black')
rects2 = ax.bar(x, size_ratios, w, label="Objective Size-Thresholded (h <= l0)", color="#5cb85c", alpha=0.85, edgecolor='black')
rects3 = ax.bar(x + w, [min(r, 10.0) for r in corner_ratios], w, label="Geometric Corner-to-Core (Mean Far / Min Core)*", color="#0275d8", alpha=0.85, edgecolor='black')

ax.axhline(2.0, color='crimson', linestyle='--', linewidth=1.8, label="Gate 06 Requirement (2.0x)")
ax.set_xticks(x)
ax.set_xticklabels(case_labels, fontsize=11, fontweight='bold')
ax.set_ylabel("Coarsening Ratio (Far-Field / Core)", fontsize=11, fontweight='bold')
ax.set_title("(a) Coarsening Ratio by Metric Formulation", fontsize=12, fontweight='bold')
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9)
ax.grid(axis='y', linestyle=':', alpha=0.6)
ax.set_ylim(0, 11)

# Annotate bars
for i in range(len(cases)):
    ax.annotate("%.2fx" % base_ratios[i], (x[i] - w, base_ratios[i] + 0.15), ha='center', fontsize=8, fontweight='bold')
    ax.annotate("%.2fx" % size_ratios[i], (x[i], size_ratios[i] + 0.15), ha='center', fontsize=8, fontweight='bold')
    ax.annotate("%.1fx" % corner_ratios[i], (x[i] + w, min(corner_ratios[i], 10.0) + 0.15), ha='center', fontsize=8, fontweight='bold', color="#0275d8")

# -------------------------------------------------------------
# Panel (b): Misclassified Process Zone Elements in Baseline Audit
# -------------------------------------------------------------
ax = axes[0, 1]
total_elems = [data[c]["total_elements"] for c in cases]
base_pz = [data[c]["baseline_audit"]["process_zone_count"] for c in cases]
actual_pz = [data[c]["size_thresholded_partitioning"]["pz_count"] for c in cases]
misclassified = [actual_pz[i] - base_pz[i] for i in range(len(cases))]

rects_base = ax.bar(x - 0.15, base_pz, 0.3, label="Counted in Process Zone (Baseline)", color="#5bc0de", edgecolor='black')
rects_actual = ax.bar(x + 0.15, actual_pz, 0.3, label="Actual Refined Elements (h <= l0)", color="#f0ad4e", edgecolor='black')

ax.set_xticks(x)
ax.set_xticklabels(case_labels, fontsize=11, fontweight='bold')
ax.set_ylabel("Element Count", fontsize=11, fontweight='bold')
ax.set_title("(b) Refined Elements: Counted vs Misclassified into Far-Field", fontsize=12, fontweight='bold')
ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
ax.grid(axis='y', linestyle=':', alpha=0.6)

for i in range(len(cases)):
    pct_missed = (float(misclassified[i]) / actual_pz[i]) * 100.0 if actual_pz[i] > 0 else 0
    if misclassified[i] > 0:
        ax.annotate("+%d\n(%.0f%% dumped to FF)" % (misclassified[i], pct_missed),
                    (x[i] + 0.15, actual_pz[i] + 1500), ha='center', fontsize=8, fontweight='bold', color='darkred')

# -------------------------------------------------------------
# Panel (c): Case 2 Element Size Decay Curve (Distance from Notch)
# -------------------------------------------------------------
ax = axes[1, 0]
# Plot Case 2 and Case 3 corner vs core dynamic ranges
c2_min = data["case_2"]["min_h_um"]
c2_med = data["case_2"]["median_h_mm"] * 1000.0
c2_c_mean = data["case_2"]["geometric_corner_far_field"]["mean_corner_h_um"]
c2_c_max = data["case_2"]["geometric_corner_far_field"]["max_corner_h_um"]

c3_min = data["case_3"]["min_h_um"]
c3_med = data["case_3"]["median_h_mm"] * 1000.0
c3_c_mean = data["case_3"]["geometric_corner_far_field"]["mean_corner_h_um"]
c3_c_max = data["case_3"]["geometric_corner_far_field"]["max_corner_h_um"]

categories = ["Min Element\n(Crack Core)", "Median\nElement", "Corner Far-Field\n(Mean)", "Corner Far-Field\n(Maximum)"]
y_c2 = [c2_min, c2_med, c2_c_mean, c2_c_max]
y_c3 = [c3_min, c3_med, c3_c_mean, c3_c_max]

x_cat = np.arange(len(categories))
ax.plot(x_cat, y_c2, 'o-', color='#e74c3c', linewidth=2.5, markersize=8, label="Case 2 (Off-Axis Hole, l0=7.5 um)")
for i, val in enumerate(y_c2):
    ax.annotate("%.2f um" % val, (x_cat[i], val * 1.15), ha='center', fontsize=8.5, fontweight='bold', color='#e74c3c')

ax.set_xticks(x_cat)
ax.set_xticklabels(categories, fontsize=10, fontweight='bold')
ax.set_ylabel("Element Equivalent Size h (um)", fontsize=11, fontweight='bold')
ax.set_yscale('log')
ax.set_title("(c) Case 2 Physical Element Size Scaling Across Zones", fontsize=12, fontweight='bold')
ax.grid(True, which="both", linestyle=':', alpha=0.6)
ax.legend(loc="upper left", fontsize=9.5)
ax.set_ylim(0.2, 50)

# -------------------------------------------------------------
# Panel (d): Case 3 Physical Element Size Scaling Across Zones
# -------------------------------------------------------------
ax = axes[1, 1]
ax.plot(x_cat, y_c3, 's-', color='#2980b9', linewidth=2.5, markersize=8, label="Case 3 (Notched Plate with Pins, l0=285 um)")
for i, val in enumerate(y_c3):
    ax.annotate("%.1f um\n(%.3f mm)" % (val, val/1000.0), (x_cat[i], val * 1.15), ha='center', fontsize=8.5, fontweight='bold', color='#2980b9')

ax.set_xticks(x_cat)
ax.set_xticklabels(categories, fontsize=10, fontweight='bold')
ax.set_ylabel("Element Equivalent Size h (um)", fontsize=11, fontweight='bold')
ax.set_yscale('log')
ax.set_title("(d) Case 3 Physical Element Size Scaling Across Zones", fontsize=12, fontweight='bold')
ax.grid(True, which="both", linestyle=':', alpha=0.6)
ax.legend(loc="upper left", fontsize=9.5)
ax.set_ylim(20, 3000)

plt.tight_layout()

out_dir = os.path.join(REPO_ROOT, "results", "figures")
png_path = os.path.join(out_dir, "fig_f1825_coarsening_metric_diagnosis.png")
pdf_path = os.path.join(out_dir, "fig_f1825_coarsening_metric_diagnosis.pdf")

plt.savefig(png_path, dpi=300)
plt.savefig(pdf_path)
plt.close()

print("FIGURES GENERATED:")
print("PNG: %s" % png_path)
print("PDF: %s" % pdf_path)
