# -*- coding: utf-8 -*-
"""
scripts/validation/compare_f1678_vs_coarse.py
============================================
Compares refined Method A (20,213 physical elements) against coarse coupled
fracture baseline (2,906 physical elements, Job 1421063.mmaster02).

Produces:
1. Quantitative JSON comparison report
2. P(u) Load-displacement comparison curve (PNG)
3. Energy balance verification plot (PNG)
4. Crack trajectory and deflection plot (PNG)
"""
from __future__ import print_function
import os
import sys
import json
import csv
import math

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    PLT_AVAILABLE = True
except ImportError:
    PLT_AVAILABLE = False


def load_rf_csv(csv_path):
    u_vals = []
    p_vals = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        # Identify columns
        u_col = 3 if 'u2' in header[3].lower() else 1
        p_col = 4 if 'rf2' in header[4].lower() else 2
        for row in reader:
            if not row or len(row) < 5:
                continue
            try:
                u = float(row[u_col])
                p = float(row[p_col])
                u_vals.append(u)
                p_vals.append(p)
            except ValueError:
                pass
    return u_vals, p_vals


def run_comparison(coarse_summary_json, coarse_rf_csv, refined_summary_json, refined_rf_csv, refined_energy_csv, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(coarse_summary_json, 'r') as f:
        coarse_sum = json.load(f)
    with open(refined_summary_json, 'r') as f:
        refined_sum = json.load(f)

    u_coarse, p_coarse = load_rf_csv(coarse_rf_csv)
    u_refined, p_refined = load_rf_csv(refined_rf_csv)

    p_max_coarse = coarse_sum.get("peak_force_kN", max(p_coarse) if p_coarse else 0.0)
    u_peak_coarse = coarse_sum.get("peak_disp_mm", 0.0)

    p_max_refined = refined_sum.get("peak_reaction_force_kN", max(p_refined) if p_refined else 0.0)
    u_peak_refined = refined_sum.get("peak_displacement_mm", 0.0)

    delta_p_max = p_max_refined - p_max_coarse
    delta_p_max_pct = (delta_p_max / p_max_coarse * 100.0) if p_max_coarse > 0 else 0.0

    comparison_report = {
        "coarse_model": {
            "name": "PK_HOLE_COARSE_JOB1 (1421063.mmaster02)",
            "n_physical_elements": 2906,
            "peak_force_kN": p_max_coarse,
            "peak_disp_mm": u_peak_coarse,
            "final_disp_mm": coarse_sum.get("last_disp_mm", u_coarse[-1] if u_coarse else 0.0),
            "final_force_kN": coarse_sum.get("last_rf2_kN", p_coarse[-1] if p_coarse else 0.0)
        },
        "refined_method_a": {
            "name": "M1_HOLE_F1664_METHOD_A_PROD (1421142.mmaster02)",
            "n_physical_elements": refined_sum.get("n_physical_elements", 20213),
            "peak_force_kN": p_max_refined,
            "peak_disp_mm": u_peak_refined,
            "final_disp_mm": refined_sum.get("final_displacement_mm", u_refined[-1] if u_refined else 0.0),
            "final_force_kN": refined_sum.get("final_reaction_force_kN", p_refined[-1] if p_refined else 0.0),
            "w_ext_kNmm": refined_sum.get("external_work_w_ext_kNmm", 0.0),
            "e_elastic_kNmm": refined_sum.get("final_e_elastic_kNmm", 0.0),
            "e_fracture_kNmm": refined_sum.get("final_e_fracture_kNmm", 0.0),
            "e_total_kNmm": refined_sum.get("final_e_total_kNmm", 0.0),
            "delta_e_discrepancy_kNmm": refined_sum.get("energy_balance_discrepancy_delta_E_kNmm", 0.0),
            "delta_e_discrepancy_pct": refined_sum.get("energy_balance_discrepancy_pct", 0.0)
        },
        "comparison_metrics": {
            "delta_peak_force_kN": delta_p_max,
            "delta_peak_force_pct": delta_p_max_pct,
            "mesh_refinement_ratio": 20213.0 / 2906.0,
            "physical_acceptance_band_kN": [0.60, 0.80],
            "peak_in_acceptance_band": (0.60 <= p_max_refined <= 0.80),
            "post_peak_softening_observed": (refined_sum.get("final_reaction_force_kN", 1.0) < p_max_refined * 0.5)
        },
        "trajectory": refined_sum.get("trajectory", {})
    }

    out_json = os.path.join(out_dir, "f1678_method_a_coarse_comparison.json")
    with open(out_json, 'w') as f:
        json.dump(comparison_report, f, indent=2)
    print("Wrote comparison report to: %s" % out_json)

    # Generate Figures if matplotlib is available
    if PLT_AVAILABLE:
        # 1. P(u) curve
        plt.figure(figsize=(8, 6))
        plt.plot([u * 1000.0 for u in u_coarse], p_coarse, 'k--', label='Coarse Baseline (2,906 elems, Job 1421063)', linewidth=1.8)
        plt.plot([u * 1000.0 for u in u_refined], p_refined, 'r-', label='Method A Adapted (20,213 elems, Job 1421142)', linewidth=2.0)
        plt.axhline(0.60, color='gray', linestyle=':', label='Pandey-Kumar Band (0.60 - 0.80 kN)')
        plt.axhline(0.80, color='gray', linestyle=':')
        plt.xlabel('Displacement u [$\mu$m]', fontsize=12)
        plt.ylabel('Reaction Force P [kN]', fontsize=12)
        plt.title('Mode-I Plate with Hole: Load-Displacement Response\nMethod A Refined (20,213 elems) vs Coarse Baseline (2,906 elems)', fontsize=13)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(loc='upper right', fontsize=10)
        plt.tight_layout()
        p_curve_path = os.path.join(out_dir, "f1678_method_a_load_displacement_comparison.png")
        plt.savefig(p_curve_path, dpi=300)
        plt.close()
        print("Generated P(u) plot: %s" % p_curve_path)

        # 2. Energy Balance Plot if energy CSV exists
        if os.path.exists(refined_energy_csv):
            steps = []
            u_energy = []
            e_elas = []
            e_frac = []
            e_tot = []
            with open(refined_energy_csv, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('Step'):
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 7:
                        try:
                            kstep = int(parts[0])
                            ttot = float(parts[2])
                            # In Step 1: u = 0.005 * ttot; In Step 2: u = 0.005 + 0.007 * (ttot - 1.0)
                            u_val = 0.005 * ttot if kstep == 1 else (0.005 + 0.007 * (ttot - 1.0))
                            u_energy.append(u_val * 1000.0)
                            e_elas.append(float(parts[4]))
                            e_frac.append(float(parts[5]))
                            e_tot.append(float(parts[6]))
                        except ValueError:
                            pass

            if u_energy:
                plt.figure(figsize=(8, 6))
                plt.plot(u_energy, e_elas, 'b-', label='Elastic Energy $E_{\mathrm{elastic}}$', linewidth=1.8)
                plt.plot(u_energy, e_frac, 'g-', label='Fracture Energy $E_{\mathrm{fracture}}$', linewidth=1.8)
                plt.plot(u_energy, e_tot, 'm--', label='Total UEL Energy $E_{\mathrm{total}}$', linewidth=2.0)
                plt.xlabel('Displacement u [$\mu$m]', fontsize=12)
                plt.ylabel('Energy [kN$\cdot$mm]', fontsize=12)
                plt.title('Method A Production (20,213 elems): Internal Energy Partition\nElastic Strain Energy vs Monotonic Fracture Dissipation', fontsize=13)
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.legend(loc='center left', fontsize=11)
                plt.tight_layout()
                energy_plot_path = os.path.join(out_dir, "f1678_method_a_energy_balance.png")
                plt.savefig(energy_plot_path, dpi=300)
                plt.close()
                print("Generated Energy balance plot: %s" % energy_plot_path)

    return comparison_report


if __name__ == '__main__':
    coarse_sum = "results/validation/coarse_job1_summary.json"
    coarse_rf = "results/validation/coarse_job1_rf_u.csv"
    refined_sum = "results/validation/f1678_prod_summary.json"
    refined_rf = "results/validation/f1678_prod_rf_u.csv"
    refined_energy = "results/validation/uel_energy_balance.csv"
    out_dir = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/figures"

    if len(sys.argv) >= 7:
        coarse_sum = sys.argv[1]
        coarse_rf = sys.argv[2]
        refined_sum = sys.argv[3]
        refined_rf = sys.argv[4]
        refined_energy = sys.argv[5]
        out_dir = sys.argv[6]

    run_comparison(coarse_sum, coarse_rf, refined_sum, refined_rf, refined_energy, out_dir)
