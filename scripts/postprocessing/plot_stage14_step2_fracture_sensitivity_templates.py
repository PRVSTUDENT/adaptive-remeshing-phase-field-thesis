#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Publication-Quality Figure Generation Template for Stage-14 Step-2 errorTarget Sensitivity:
- Generates F-u reaction force comparison plots
- Generates multi-quantity summary plots (K0, F_max, u_peak, E_frac) vs errorTarget / element count
- Generates energy evolution and bookkeeping error evolution plots
- Generates 1D ligament spatial damage distribution d(x, y=0.5 mm) at matched displacement states
"""

from __future__ import print_function
import os
import sys
import json
import argparse

# Reference Values
REFERENCE_ANCHOR = {
    'label': "Fixed Reference S1 (15,192 FE)",
    'base_elements': 15192,
    'K0': 137.945520,
    'F_max': 0.757778,
    'u_peak': 0.005857,
    'E_frac': 2.340220,
    'eps_book': 0.7607
}

ET1_BASELINE = {
    'label': "ET1 Adaptive Baseline (14,483 FE)",
    'base_elements': 14483,
    'K0': 137.909558,
    'F_max': 0.743701,
    'u_peak': 0.005733,
    'E_frac': 2.285469,
    'eps_book': 1.104771
}

CASES_METADATA = {
    'ET1': {'error_target': 1.0, 'base_elements': 14483, 'status': 'COMPLETED_BASELINE'},
    'ET2': {'error_target': 2.0, 'base_elements': 6112,  'status': 'RUNNING_1410357'},
    'ET3': {'error_target': 3.0, 'base_elements': 5189,  'status': 'RUNNING_1410358'},
    'ET5': {'error_target': 5.0, 'base_elements': 4692,  'status': 'RUNNING_1410359'}
}

def export_plot_manifest(output_dir="results/figures/mode1_gate6b"):
    """
    Exports figure specification manifest detailing figure titles, axes, units, and data sources.
    """
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception:
            pass
            
    manifest = {
        'figures': [
            {
                'id': "fig_mode1_stage14_step2_fu_comparison",
                'title': "Mode-I Reaction Force vs Displacement: errorTarget Sensitivity (ET=1%, 2%, 3%, 5%)",
                'x_axis': "Displacement $u$ [mm]",
                'y_axis': "Reaction Force $F$ [kN]",
                'series': [
                    "Fixed Reference S1 (15,192 FE)",
                    "ET=1.0% Adaptive (14,483 FE, Target-Like)",
                    "ET=2.0% Adaptive (6,112 FE)",
                    "ET=3.0% Adaptive (5,189 FE)",
                    "ET=5.0% Adaptive (4,692 FE)"
                ]
            },
            {
                'id': "fig_mode1_stage14_step2_metrics_summary",
                'title': "Mode-I Multi-Quantity Mechanical Metrics vs errorTarget Refinement",
                'subpanels': [
                    "Initial Structural Stiffness $K_0$ [kN/mm]",
                    "Peak Reaction Force $F_{\\max}$ [kN]",
                    "Peak Displacement $u(F_{\\max})$ [mm]",
                    "Broken-State Functional $E_{\\mathrm{frac}}$ [mJ]"
                ]
            },
            {
                'id': "fig_mode1_stage14_step2_matched_phase_profiles",
                'title': "Ligament Phase-Field Profiles $d(x, y=0.5\\,\\mathrm{mm})$ at Matched Displacements",
                'matched_displacements_mm': [0.0010, 0.0030, 0.0050, 0.005733, 0.005857, 0.0060, 0.0065, 0.0070]
            },
            {
                'id': "fig_mode1_stage14_step2_energy_partitioning",
                'title': "Energy Components and Bookkeeping Residual Evolution",
                'components': ["External Work $W_{\\mathrm{ext}}$", "Fracture Functional $E_{\\mathrm{frac}}$", "Elastic Energy $E_{\\mathrm{elas}}$", "Bookkeeping Residual $\\varepsilon_{\\mathrm{book}}$ [\\%]"]
            }
        ]
    }
    manifest_path = os.path.join(output_dir, "stage14_step2_figure_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print("Exported figure manifest to %s" % manifest_path)
    return manifest_path

def generate_figure_template_report():
    print("================================================================================")
    print("STAGE-14 STEP-2 PUBLICATION FIGURE GENERATION TEMPLATES & MANIFEST")
    print("================================================================================")
    print("1. Fig 1: F-u Reaction Force Overlay (Fixed Ref vs ET1, ET2, ET3, ET5)")
    print("2. Fig 2: Multi-Quantity Metrics Summary (K0, F_max, u_peak, E_frac vs errorTarget)")
    print("3. Fig 3: Matched Ligament Phase-Field Profiles d(x, y=0.5 mm)")
    print("4. Fig 4: Global Energy Partitioning & Bookkeeping Residual Evolution")
    print("================================================================================")

def main():
    parser = argparse.ArgumentParser(description="Plot templates for Stage-14 Step-2 errorTarget batch")
    parser.add_argument('--export-manifest', action='store_true', help="Export figure specification manifest")
    parser.add_argument('--output-dir', default="results/figures/mode1_gate6b", help="Output directory")
    args = parser.parse_args()
    
    generate_figure_template_report()
    if args.export_manifest:
        export_plot_manifest(args.output_dir)

if __name__ == "__main__":
    main()
