# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_f1728_five_case_figure.py
Assembles a high-resolution 5-panel comparative publication figure showing the
Method A adaptive meshes across all Five Benchmark Geometries:
  - Case 1: Mode-I Edge-Cracked Plate (Section 4.1)
  - Case 2: Original Off-Axis Hole Plate (Thesis Benchmark)
  - Case 3: Rectangular Notched Plate with Hole and Pin Holes (Section 4.3)
  - Case 4: Five-Hole Plate (Section 4.5)
  - Case 5: Seven-Hole Plate (Section 4.6)
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

def generate_five_case_figure(out_png, out_pdf=None):
    img_paths = [
        ("Case 1: Mode-I Edge-Cracked Plate (Sec. 4.1)\nAdapted: 14,147 el (Target: 13,941 el) | PASS",
         "figures/f1727_three_geometries/fig_model_b_4_adapted_mesh.png"),
        ("Case 2: Off-Axis Circular Hole Plate (Thesis)\nAdapted: 23,965 el (Distal Resolved) | PASS",
         "figures/f1727_three_geometries/fig_model_c_4_adapted_mesh.png"),
        ("Case 3: Notched Plate with Hole & Pins (Sec. 4.3)\nAdapted: 12,284 el | PARTIALLY_VALIDATED (Single Corridor)",
         "figures/f1727_three_geometries/fig_model_a_4_adapted_mesh.png"),
        ("Case 4: Five-Hole Plate (Sec. 4.5)\nAdapted: 13,017 el (Target: 12,944 el) | PASS",
         "figures/pandey_kumar_fig22_25_reproduction/fig_f1725_figure_1_five_way_mesh_comparison.png"),
        ("Case 5: Seven-Hole Plate (Sec. 4.6)\nAdapted: 15,708 el (Target: 15,714 el) | PASS",
         "figures/pandey_kumar_fig22_25_reproduction/fig_f1726_figure_1_full_domain_mesh_comparison.png")
    ]
    
    fig, axes = plt.subplots(1, 5, figsize=(25, 6))
    plt.subplots_adjust(wspace=0.15, top=0.85, bottom=0.05, left=0.02, right=0.98)
    
    fig.suptitle(
        "Method A Adaptive Remeshing Framework — Five-Geometry Benchmark Verification\n"
        "Unified Native Engine Evaluation | Status: FIVE_CASE_METHOD_A_FRAMEWORK_PARTIALLY_VALIDATED",
        fontsize=16, fontweight='bold', y=0.98
    )
    
    for i, (title, p) in enumerate(img_paths):
        ax = axes[i]
        if os.path.exists(p):
            im = Image.open(p)
            ax.imshow(im)
        else:
            ax.text(0.5, 0.5, f"Image Missing:\n{p}", ha='center', va='center')
        ax.set_title(title, fontsize=11, fontweight='semibold', pad=10)
        ax.axis('off')
        
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    print("Saved PNG to %s" % out_png)
    if out_pdf:
        plt.savefig(out_pdf, bbox_inches='tight')
        print("Saved PDF to %s" % out_pdf)
    plt.close()

if __name__ == "__main__":
    generate_five_case_figure(
        "results/figures/fig_f1728_five_case_mesh_comparison.png",
        "results/figures/fig_f1728_five_case_mesh_comparison.pdf"
    )
