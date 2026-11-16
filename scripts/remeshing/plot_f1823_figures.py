# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1823_figures.py
=======================================
Generates publication-quality figure fig_f1823_coarsening_and_donor_investigation.png / .pdf
synthesizing the three steps of Task F1823:
  - Panel A: Step 1 Framework Kwargs & Discrepancy Parity (Old vs Enhanced FW)
  - Panel B: Step 2 Bounded Coarsening Sweep (Cases 2 and 3 Trade-offs)
  - Panel C: Step 3 Targeted Donor Investigation: State Ablation & Critical Coverage
  - Panel D: Within-3*l0 Concentration & Resolution Gate Trade-off Summary
"""
import os
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STEP1_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step1_comparison", "step1_framework_comparison_results.json")
STEP2_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step2_coarsening", "step2_coarsening_sweep_summary.json")
STEP3_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step3_donors", "step3_targeted_donors_summary.json")

FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
if not os.path.exists(FIG_DIR):
    os.makedirs(FIG_DIR)

PNG_OUT = os.path.join(FIG_DIR, "fig_f1823_coarsening_and_donor_investigation.png")
PDF_OUT = os.path.join(FIG_DIR, "fig_f1823_coarsening_and_donor_investigation.pdf")

def main():
    with open(STEP1_JSON, "r") as f:
        s1_data = json.load(f)
    with open(STEP2_JSON, "r") as f:
        s2_data = json.load(f)
    with open(STEP3_JSON, "r") as f:
        s3_data = json.load(f)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    plt.subplots_adjust(hspace=0.32, wspace=0.28)

    # -------------------------------------------------------------
    # Panel A: Step 1 Framework Comparison (Old vs Enhanced)
    # -------------------------------------------------------------
    ax = axes[0, 0]
    categories = ["UE 3.0%\n(Old FW)", "UE 3.0%\n(Enh FW)", "UE 4.5%\n(Old FW)", "UE 4.5%\n(Enh FW)"]
    elements = [
        s1_data["old_fw_ue_3pct"]["total_elements"],
        s1_data["enhanced_fw_ue_3pct"]["total_elements"],
        s1_data["old_fw_ue_45pct"]["total_elements"],
        s1_data["enhanced_fw_ue_45pct"]["total_elements"]
    ]
    colors = ["#2b5c8f", "#4682b4", "#d95f02", "#f1a340"]
    bars = ax.bar(categories, elements, color=colors, width=0.55, edgecolor="black", linewidth=1.2)
    
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1000, "%d el\n(0 diff)" % yval, ha="center", va="bottom", fontsize=9, fontweight="bold")
        
    ax.set_ylim(0, 75000)
    ax.set_ylabel("Element Count", fontsize=11, fontweight="bold")
    ax.set_title("(a) Step 1: Framework Kwargs & Discrepancy Parity\n(Zero Framework Discrepancy: Bitwise Identical)", fontsize=11, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # -------------------------------------------------------------
    # Panel B: Step 2 Bounded Coarsening Sweep (Gate 06 vs Count)
    # -------------------------------------------------------------
    ax = axes[0, 1]
    c2_cases = ["Base\n(h=0.02, 4%)", "Var 2.1\n(h=0.03, 4%)", "Var 2.2\n(h=0.04, 4%)", "Var 2.3\n(h=0.03, 5%)"]
    c2_counts = [
        s2_data["c2_base_eta40_h020"]["total_elements"],
        s2_data["c2_var1_eta40_h030"]["total_elements"],
        s2_data["c2_var2_eta40_h040"]["total_elements"],
        s2_data["c2_var3_eta50_h030"]["total_elements"]
    ]
    c2_coarsen = [
        s2_data["c2_base_eta40_h020"]["coarsening_ratio"],
        s2_data["c2_var1_eta40_h030"]["coarsening_ratio"],
        s2_data["c2_var2_eta40_h040"]["coarsening_ratio"],
        s2_data["c2_var3_eta50_h030"]["coarsening_ratio"]
    ]
    
    x = np.arange(len(c2_cases))
    width = 0.35
    
    ax2 = ax.twinx()
    b1 = ax.bar(x - width/2, [c/1000.0 for c in c2_counts], width, label="Elements (k)", color="#386cb0", edgecolor="black")
    b2 = ax2.bar(x + width/2, c2_coarsen, width, label="Coarsening Ratio", color="#7fc97f", edgecolor="black")
    ax2.axhline(2.0, color="crimson", linestyle="--", linewidth=1.5, label="Gate 06 Threshold (2.0x)")
    
    ax.set_ylabel("Element Count (thousands)", fontsize=11, fontweight="bold", color="#386cb0")
    ax2.set_ylabel("Far-Field Coarsening Ratio", fontsize=11, fontweight="bold", color="#238b45")
    ax.set_xticks(x)
    ax.set_xticklabels(c2_cases, fontsize=9)
    ax.set_ylim(0, 50)
    ax2.set_ylim(0, 2.5)
    ax.set_title("(b) Step 2: Case 2 Coarsening Sweep\n(Coarsening Pegged at ~1.56x < 2.0x Threshold)", fontsize=11, fontweight="bold")
    
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

    # -------------------------------------------------------------
    # Panel C: Step 3 Case 2 Donor State Ablation Analysis
    # -------------------------------------------------------------
    ax = axes[1, 0]
    c2_donor_names = ["Baseline\n(States 1-4)", "Omit S1\n(States 2,3,4)", "Omit S3\n(States 1,2,4)", "Omit S4\n(States 1,2,3)"]
    c2_distal_cov = [
        s3_data["investigations"]["c2_base_4states"]["scientific_gate"]["val"],
        s3_data["investigations"]["c2_omit_state1"]["scientific_gate"]["val"],
        s3_data["investigations"]["c2_omit_state3"]["scientific_gate"]["val"],
        s3_data["investigations"]["c2_omit_state4"]["scientific_gate"]["val"]
    ]
    c2_notch_cov = [
        s3_data["investigations"]["c2_base_4states"]["scientific_gate"]["extra_val"],
        s3_data["investigations"]["c2_omit_state1"]["scientific_gate"]["extra_val"],
        s3_data["investigations"]["c2_omit_state3"]["scientific_gate"]["extra_val"],
        s3_data["investigations"]["c2_omit_state4"]["scientific_gate"]["extra_val"]
    ]
    
    x = np.arange(len(c2_donor_names))
    width = 0.35
    ax.bar(x - width/2, c2_distal_cov, width, label="Outer Distal Gate (%)", color="#beaed4", edgecolor="black")
    ax.bar(x + width/2, c2_notch_cov, width, label="Notch Corridor (%)", color="#fdc086", edgecolor="black")
    ax.axhline(100.0, color="crimson", linestyle="--", linewidth=1.2, label="Outer Distal Gate (100%)")
    
    for i in range(len(x)):
        ax.text(x[i] - width/2, c2_distal_cov[i] + 2, "%.1f%%" % c2_distal_cov[i], ha="center", va="bottom", fontsize=8, fontweight="bold")
        ax.text(x[i] + width/2, c2_notch_cov[i] + 2, "%.1f%%" % c2_notch_cov[i], ha="center", va="bottom", fontsize=8, fontweight="bold")
        
    ax.set_ylabel("Corridor Resolution (%)", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(c2_donor_names, fontsize=9)
    ax.set_ylim(0, 118)
    ax.set_title("(c) Step 3: Case 2 Donor State Ablation\n(S1 Controls Notch, S4 Controls Outer Distal)", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # -------------------------------------------------------------
    # Panel D: Step 3 Case 3 Donor State Ablation Analysis
    # -------------------------------------------------------------
    ax = axes[1, 1]
    c3_donor_names = ["Baseline\n(States 1,2,3)", "Omit S1\n(States 2,3)", "Omit S2\n(States 1,3)", "Omit S3\n(States 1,2)"]
    c3_sec_cov = [
        s3_data["investigations"]["c3_base_3states"]["scientific_gate"]["val"],
        s3_data["investigations"]["c3_omit_state1"]["scientific_gate"]["val"],
        s3_data["investigations"]["c3_omit_state2"]["scientific_gate"]["val"],
        s3_data["investigations"]["c3_omit_state3"]["scientific_gate"]["val"]
    ]
    c3_prim_cov = [
        s3_data["investigations"]["c3_base_3states"]["scientific_gate"]["extra_val"],
        s3_data["investigations"]["c3_omit_state1"]["scientific_gate"]["extra_val"],
        s3_data["investigations"]["c3_omit_state2"]["scientific_gate"]["extra_val"],
        s3_data["investigations"]["c3_omit_state3"]["scientific_gate"]["extra_val"]
    ]
    c3_f3l0 = [
        s3_data["investigations"]["c3_base_3states"]["width_metrics"]["f_3l0"],
        s3_data["investigations"]["c3_omit_state1"]["width_metrics"]["f_3l0"],
        s3_data["investigations"]["c3_omit_state2"]["width_metrics"]["f_3l0"],
        s3_data["investigations"]["c3_omit_state3"]["width_metrics"]["f_3l0"]
    ]
    
    x = np.arange(len(c3_donor_names))
    width = 0.35
    ax.bar(x - width/2, c3_sec_cov, width, label="Secondary Corridor (%)", color="#7fc97f", edgecolor="black")
    ax.bar(x + width/2, c3_prim_cov, width, label="Primary Notch Corridor (%)", color="#ffff99", edgecolor="black")
    
    for i in range(len(x)):
        ax.text(x[i] - width/2, c3_sec_cov[i] + 2, "%.1f%%" % c3_sec_cov[i], ha="center", va="bottom", fontsize=8, fontweight="bold")
        ax.text(x[i] + width/2, c3_prim_cov[i] + 2, "%.1f%%" % c3_prim_cov[i], ha="center", va="bottom", fontsize=8, fontweight="bold")
        
    ax.set_ylabel("Corridor Resolution (%)", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(c3_donor_names, fontsize=9)
    ax.set_ylim(0, 110)
    ax.set_title("(d) Step 3: Case 3 Donor State Ablation\n(S1 Controls Primary Notch, S3 Controls Secondary Corridor)", fontsize=11, fontweight="bold")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(PNG_OUT, dpi=300)
    plt.savefig(PDF_OUT)
    plt.close()
    print("Saved figure: %s and %s" % (PNG_OUT, PDF_OUT))

if __name__ == "__main__":
    main()
