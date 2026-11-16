# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1816_figures.py
=======================================
Task F1816: Multi-Step Refinement Narrowing Across Four Canonical Benchmarks.
Generates comprehensive publication figures comparing:
  1. F1812 Baseline (UNIFORM_ERROR, Full Multi-State Envelope)
  2. Step 1: MINIMUM_MAXIMUM Sizing (eta_max=1%, eta_min=5%, meshBias=7)
  3. Step 2 Variant 2b: Reduced 2-State Envelope (Breach/Arrest + Terminal)
  4. Step 2 Variant 2a: Overlapping Native Rules (Multi-step CAE rules)

Outputs:
  - results/figures/fig_f1816_refinement_width_comparison.png
  - results/figures/fig_f1816_refinement_width_comparison.pdf
"""
from __future__ import print_function
import os
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
if not os.path.exists(FIG_DIR):
    os.makedirs(FIG_DIR)

STEP1_SUMMARY = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step1_minmax", "step1_minmax_summary.json")
STEP2_SUMMARY = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope", "step2_envelope_summary.json")

def load_data():
    with open(STEP1_SUMMARY, "r") as f:
        d1 = json.load(f)
    with open(STEP2_SUMMARY, "r") as f:
        d2 = json.load(f)
    return d1, d2

def plot_synthesis_figure():
    d1, d2 = load_data()
    cases = ["case_1", "case_2", "case_3", "case_5"]
    case_labels = [
        "Case 1\n(Edge-Cracked)",
        "Case 2\n(Off-Axis Hole)",
        "Case 3\n(Notched Pin-Hole)",
        "Case 5\n(Seven Holes)"
    ]
    
    # Configurations:
    # 0: F1812 Baseline
    # 1: Step 1 (Min/Max Sizing)
    # 2: Step 2b (Reduced 2-State Envelope)
    # 3: Step 2a (Overlapping Rules)
    
    config_labels = [
        "F1812 Baseline (Adopted)",
        "Step 1: Min/Max Sizing",
        "Step 2b: 2-State Envelope",
        "Step 2a: Overlapping Rules"
    ]
    colors = ["#1b5e20", "#d32f2f", "#f57c00", "#1976d2"]
    
    # Extract element counts
    el_data = np.zeros((4, 4))
    # Extract width within 3*l0 (%)
    w3_data = np.zeros((4, 4))
    # Extract scientific gate values (%)
    gate_data = np.zeros((4, 4))
    gate_thresholds = [95.0, 100.0, 90.0, 90.0]
    
    for i, cid in enumerate(cases):
        # Baseline F1812
        base = d2["variant_2b_reduced"][cid]["f1812_baseline"]
        el_data[0, i] = base["elements"]
        w3_data[0, i] = base["f_3l0"]
        gate_data[0, i] = base["gate_val"]
        
        # Step 1: Min/Max
        s1 = d1["cases"][cid]
        el_data[1, i] = s1["total_elements"]
        w3_data[1, i] = s1["width_metrics"].get("f_3l0", s1["width_metrics"].get("pct_within_3l0", 0.0))
        gate_data[1, i] = s1["scientific_gate_value"]
        
        # Step 2b: Reduced Envelope
        s2b = d2["variant_2b_reduced"][cid]
        el_data[2, i] = s2b["elements"]
        w3_data[2, i] = s2b["width_metrics"]["f_3l0"]
        gate_data[2, i] = s2b["scientific_gate"]["val"]
        
        # Step 2a: Overlapping Rules
        s2a = d2["variant_2a_overlapping"][cid]
        el_data[3, i] = s2a["elements"]
        w3_data[3, i] = s2a["width_metrics"]["f_3l0"]
        gate_data[3, i] = s2a["scientific_gate"]["val"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    plt.subplots_adjust(hspace=0.32, wspace=0.25)
    
    x = np.arange(4)
    bar_w = 0.20
    
    # ----------------------------------------------------
    # Panel (a): Band Width Metric (Fine Elements within 3*l0)
    # ----------------------------------------------------
    ax = axes[0, 0]
    for k in range(4):
        offset = (k - 1.5) * bar_w
        rects = ax.bar(x + offset, w3_data[k], bar_w, label=config_labels[k], color=colors[k], alpha=0.85, edgecolor='black', linewidth=0.6)
        for r in rects:
            h = r.get_height()
            if h > 0.1:
                y_off = 2 if (k % 2 == 0) else 7
                ax.annotate("%.1f%%" % h, xy=(r.get_x() + r.get_width()/2, h), xytext=(0, y_off),
                            textcoords="offset points", ha='center', va='bottom', fontsize=6.8, rotation=0)
    ax.set_ylabel("Fine Elements within 3$\\ell_0$ of Crack Path (%)", fontsize=9, fontweight='bold')
    ax.set_title("(a) Refinement Band Concentration (Higher = More Localized)", fontsize=11, fontweight='bold', loc='left')
    ax.set_xticks(x)
    ax.set_xticklabels(case_labels, fontsize=9)
    ax.set_ylim(0, 38)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='upper right')
    
    # ----------------------------------------------------
    # Panel (b): Mesh Element Counts
    # ----------------------------------------------------
    ax = axes[0, 1]
    for k in range(4):
        offset = (k - 1.5) * bar_w
        rects = ax.bar(x + offset, el_data[k], bar_w, label=config_labels[k], color=colors[k], alpha=0.85, edgecolor='black', linewidth=0.6)
        for r in rects:
            h = r.get_height()
            ax.annotate("%d" % h, xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 2),
                        textcoords="offset points", ha='center', va='bottom', fontsize=6.5, rotation=45)
    ax.set_ylabel("Total Physical Element Count", fontsize=9, fontweight='bold')
    ax.set_title("(b) Discretization Cost & Mesh Ballooning", fontsize=11, fontweight='bold', loc='left')
    ax.set_xticks(x)
    ax.set_xticklabels(case_labels, fontsize=9)
    ax.set_ylim(0, 105000)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='upper left')
    
    # ----------------------------------------------------
    # Panel (c): Scientific Resolution Gate Performance
    # ----------------------------------------------------
    ax = axes[1, 0]
    for k in range(4):
        offset = (k - 1.5) * bar_w
        rects = ax.bar(x + offset, gate_data[k], bar_w, label=config_labels[k], color=colors[k], alpha=0.85, edgecolor='black', linewidth=0.6)
        for r in rects:
            h = r.get_height()
            ax.annotate("%.1f%%" % h, xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 2),
                        textcoords="offset points", ha='center', va='bottom', fontsize=7, rotation=0)
                        
    # Draw threshold lines
    for i in range(4):
        th = gate_thresholds[i]
        ax.plot([i - 0.45, i + 0.45], [th, th], color='black', linestyle=':', linewidth=1.5)
        ax.annotate("Gate: %.0f%%" % th, xy=(i, th + 1.2), ha='center', fontsize=7.5, fontweight='bold', color='black')
        
    ax.set_ylabel("Governing Resolution Gate Coverage (%)", fontsize=9, fontweight='bold')
    ax.set_title("(c) Scientific Resolution Gate Compliance (Threshold: Dotted Line)", fontsize=11, fontweight='bold', loc='left')
    ax.set_xticks(x)
    ax.set_xticklabels([
        "Case 1: Full Ligament\n(Gate >= 95%)",
        "Case 2: Outer Distal\n(Gate = 100%)",
        "Case 3: Secondary\n(Gate >= 90%)",
        "Case 5: Inter-Hole\n(Gate >= 90%)"
    ], fontsize=8.5)
    ax.set_ylim(70, 114)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='lower right')
    
    # ----------------------------------------------------
    # Panel (d): Physical Mechanism & Pareto Synthesis
    # ----------------------------------------------------
    ax = axes[1, 1]
    ax.axis('off')
    
    summary_text = (
        "TASK F1818 REASSESSED SCIENTIFIC FINDINGS & PARETO PROOF\n"
        "----------------------------------------------------------------------------------------------------\n\n"
        "1. STEP 1 (UNIFORM_ERROR AT STRICTER TARGET; MIN/MAX UNTESTED):\n"
        "   - Shared framework hardcodes sizingMethod=UNIFORM_ERROR (line 1922); config.sizing_method\n"
        "     was silently ignored, so MINIMUM_MAXIMUM sizing was never actually exercised.\n"
        "   - Step 1 actually solved UNIFORM_ERROR with errorTarget=3.0% (vs F1812's 4.5% in Case 1),\n"
        "     causing expected element ballooning (+61.7%, 258,894 el) and band dilution.\n"
        "   - Prior 'MIN/MAX causes ballooning and is rejected' conclusion withdrawn; MIN/MAX is untested.\n\n"
        "2. STEP 2b (REDUCED 2-STATE ENVELOPE): REJECTED\n"
        "   - Fails Case 1 full-ligament gate (91.75% < 95.0%, verified) due to missing intermediate states.\n"
        "   - Case 2 element count doubled (+102.5%, 83,913 el), diluting 3*l0 concentration to 6.75%.\n"
        "   - Case 3 secondary corridor gate PASSES at 94.88% (prior 87.6% was an artifact of y in [45,75]).\n\n"
        "3. STEP 2a (OVERLAPPING NATIVE CAE RULES): REJECTED\n"
        "   - Abaqus CAE takes the envelope of minimum requested element sizes across active rules.\n"
        "   - Produces broader fine zones (Case 1: 37,511 el; Case 2: 82,869 el) and lower localization.\n"
        "   - Case 3 secondary corridor gate PASSES at 92.27% (prior 86.3% was an artifact of y in [45,75]).\n\n"
        "4. STEP 3 DECISION (CORRECTED EVIDENCE): F1812 BASELINES ADOPTED\n"
        "   - F1812 (160,144 el) remains best among tested configurations: Var 2b fails Case 1 gate,\n"
        "     and all tested variants expand element counts and dilute crack-path concentration.\n"
        "   - MINIMUM_MAXIMUM sizing remains an open question for future study (not part of F1818)."
    )
    
    ax.text(0.02, 0.98, summary_text, transform=ax.transAxes, fontsize=7.8,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#f5f5f5', edgecolor='#9e9e9e', alpha=0.9))
            
    png_path = os.path.join(FIG_DIR, "fig_f1816_refinement_width_comparison.png")
    pdf_path = os.path.join(FIG_DIR, "fig_f1816_refinement_width_comparison.pdf")
    
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.savefig(pdf_path, bbox_inches='tight')
    plt.close()
    
    print("Generated publication figures:")
    print("  PNG: %s (%d bytes)" % (png_path, os.path.getsize(png_path)))
    print("  PDF: %s (%d bytes)" % (pdf_path, os.path.getsize(pdf_path)))
    return png_path, pdf_path

if __name__ == "__main__":
    plot_synthesis_figure()
