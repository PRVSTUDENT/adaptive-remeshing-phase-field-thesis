# -*- coding: utf-8 -*-
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def load_csv(csv_path):
    records = []
    with open(csv_path, 'r') as f:
        header = f.readline().strip().split(',')
        for line in f:
            parts = line.strip().split(',')
            if not parts or len(parts) < len(header):
                continue
            rec = {}
            for k, v in zip(header, parts):
                try:
                    if '.' in v or 'e' in v or 'E' in v:
                        rec[k] = float(v)
                    else:
                        rec[k] = int(v)
                except ValueError:
                    rec[k] = v
            records.append(rec)
    return records

def generate_stage12_figures(results_dir, figures_dir):
    if not os.path.exists(figures_dir):
        os.makedirs(figures_dir)
        
    print("Generating Stage 12 Publication Figures...")
    
    # Load Stage 12 Summary
    sum_path = os.path.join(results_dir, "STAGE12_NONUNIFORM_COARSE_SUMMARY.json")
    if os.path.exists(sum_path):
        with open(sum_path, 'r') as f:
            summary = json.load(f)
    else:
        summary = {}
        
    # Load CSV data
    coarse_csv = os.path.join(results_dir, "stage12_nonuniform_coarse_elements.csv")
    adapt_csv = os.path.join(results_dir, "stage12_nonuniform_adapted_elements.csv")
    
    coarse_records = load_csv(coarse_csv) if os.path.exists(coarse_csv) else []
    adapt_records = load_csv(adapt_csv) if os.path.exists(adapt_csv) else []
    
    # Load baseline Stage 10 data for direct side-by-side comparison
    stage10_csv = "models/pandey_kumar_mode1/95_mode1_stage10_inf_companion_remesh/stage10_adapted_elements.csv"
    stage10_records = load_csv(stage10_csv) if os.path.exists(stage10_csv) else []
    
    plt.rcParams.update({
        'font.size': 10,
        'font.family': 'sans-serif',
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 13
    })
    
    # -------------------------------------------------------------
    # FIGURE 2: RAW MISESERI ERROR FIELD COMPARISON
    # -------------------------------------------------------------
    if coarse_records:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Panel A: Spatial Scatter of Raw MISESERI
        ax = axes[0, 0]
        cx = [r['cx'] for r in coarse_records]
        cy = [r['cy'] for r in coarse_records]
        err = [r['miseseri'] for r in coarse_records]
        max_e = max(err) if max(err) > 0 else 1.0
        norm_err = [e / max_e for e in err]
        
        sc = ax.scatter(cx, cy, c=norm_err, cmap='viridis', s=18, alpha=0.85, edgecolors='none')
        # Draw crack line
        ax.plot([0.0, 0.5], [0.5, 0.5], 'r-', lw=2.5, label='Initial Crack ($a=0.5$)')
        ax.plot(0.5, 0.5, 'ro', ms=6)
        # Draw corridor bounds
        ax.axhline(0.45, color='gray', ls='--', lw=1.0, alpha=0.7)
        ax.axhline(0.55, color='gray', ls='--', lw=1.0, alpha=0.7)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        ax.set_xlabel('X [mm]')
        ax.set_ylabel('Y [mm]')
        ax.set_title('(a) Non-Uniform Coarse Mesh: Normalized $e/e_{\\mathrm{max}}$')
        cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('$e / e_{\\mathrm{max}}$ (MISESERI)')
        ax.legend(loc='upper right', framealpha=0.9)
        
        # Panel B: Regional Error Distribution (Bar Chart)
        ax = axes[0, 1]
        reg_shares = summary.get('coarse_mesh_diagnostic', {}).get('regional_error_shares', {})
        if reg_shares:
            categories = ['Crack Tip\n($r \\leq 0.1$)', 'Crack Wake\n($x \\leq 0.5$)', 'Ligament\n($x > 0.5$)', 'Far-Field\n($|y-0.5| > 0.1$)']
            shares = [
                reg_shares.get('crack_tip_share', 0.0) * 100.0,
                reg_shares.get('crack_wake_share', 0.0) * 100.0,
                reg_shares.get('ligament_share', 0.0) * 100.0,
                reg_shares.get('far_field_share', 0.0) * 100.0
            ]
            colors = ['#d95f02', '#7570b3', '#1b9e77', '#e7298a']
            bars = ax.bar(categories, shares, color=colors, edgecolor='black', width=0.55)
            for b, s in zip(bars, shares):
                ax.text(b.get_x() + b.get_width()/2.0, b.get_height() + 1.0, '%.1f%%' % s, ha='center', va='bottom', fontweight='bold')
            ax.set_ylim(0, max(shares) + 12)
            ax.set_ylabel('Share of Total MISESERI Error [%]')
            ax.set_title('(b) Regional Error Share Breakdown')
            ax.grid(axis='y', ls=':', alpha=0.6)
            
        # Panel C: Error Exceedance Footprints
        ax = axes[1, 0]
        thresholds = [0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50]
        elem_fractions = []
        for th in thresholds:
            frac = sum(1 for e in norm_err if e >= th) / float(len(norm_err)) * 100.0
            elem_fractions.append(frac)
        ax.plot([th * 100.0 for th in thresholds], elem_fractions, 'o-', color='#1f77b4', lw=2.2, ms=6, label='Non-Uniform Mesh (3,019 elems)')
        ax.set_xscale('log')
        ax.set_xlabel('Error Threshold $e/e_{\\mathrm{max}}$ [%]')
        ax.set_ylabel('Elements Exceeding Threshold [%]')
        ax.set_title('(c) Error Exceedance Footprint Curve')
        ax.grid(True, which='both', ls=':', alpha=0.6)
        ax.legend(loc='upper right')
        
        # Panel D: Vertical Error Profile e(y) at select X slices
        ax = axes[1, 1]
        x_targets = [0.2, 0.5, 0.8]
        colors_x = ['#377eb8', '#e41a1c', '#4daf4a']
        for xt, col in zip(x_targets, colors_x):
            slice_pts = [(r['cy'], r['miseseri']/max_e) for r in coarse_records if abs(r['cx'] - xt) <= 0.04]
            if slice_pts:
                slice_pts.sort(key=lambda p: p[0])
                ys = [p[0] for p in slice_pts]
                es = [p[1] for p in slice_pts]
                ax.plot(ys, es, 's-', color=col, lw=1.8, ms=4, label='x = %.1f mm' % xt)
        ax.set_xlabel('Y Coordinate [mm]')
        ax.set_ylabel('Normalized Error $e / e_{\\mathrm{max}}$')
        ax.set_title('(d) Vertical Error Slices $e(y)$ Across Domain')
        ax.axvline(0.5, color='gray', ls='--', lw=1.0)
        ax.grid(True, ls=':', alpha=0.6)
        ax.legend(loc='upper right')
        
        plt.tight_layout()
        f2_png = os.path.join(figures_dir, "mode1_stage12_fig2_miseseri_field_comparison.png")
        f2_pdf = os.path.join(figures_dir, "mode1_stage12_fig2_miseseri_field_comparison.pdf")
        plt.savefig(f2_png, dpi=300)
        plt.savefig(f2_pdf)
        plt.close()
        print("Figure 2 saved: %s" % f2_png)
        
    # -------------------------------------------------------------
    # FIGURE 3: ADAPTED MESH MORPHOLOGY COMPARISON
    # -------------------------------------------------------------
    if adapt_records:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Panel A: Adapted Mesh Density / Centroid Scatter
        ax = axes[0, 0]
        cx_ad = [r['cx'] for r in adapt_records]
        cy_ad = [r['cy'] for r in adapt_records]
        h_ad = [r['h_eq'] * 1000.0 for r in adapt_records] # in microns
        
        sc_ad = ax.scatter(cx_ad, cy_ad, c=h_ad, cmap='plasma_r', s=4, alpha=0.7, edgecolors='none')
        ax.plot([0.0, 0.5], [0.5, 0.5], 'k-', lw=2.5, label='Crack Seam')
        ax.axhline(0.45, color='gray', ls='--', lw=1.0)
        ax.axhline(0.55, color='gray', ls='--', lw=1.0)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        ax.set_xlabel('X [mm]')
        ax.set_ylabel('Y [mm]')
        n_ad = len(adapt_records)
        ax.set_title('(a) Stage 12 Adapted Mesh ($N=%d$)' % n_ad)
        cbar = plt.colorbar(sc_ad, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('$h_{\\mathrm{eq}}$ [$\\mu$m]')
        ax.legend(loc='upper right')
        
        # Panel B: Element Size Distribution (CDF)
        ax = axes[0, 1]
        sorted_h_ad = np.sort(np.array(h_ad))
        cdf_ad = np.arange(1, len(sorted_h_ad) + 1) / float(len(sorted_h_ad))
        ax.plot(sorted_h_ad, cdf_ad * 100.0, '-', color='#e41a1c', lw=2.5, label='Stage 12 Non-Uniform (%d elems)' % n_ad)
        
        if stage10_records:
            h_st10 = [r['h_eq'] * 1000.0 for r in stage10_records]
            sorted_h_10 = np.sort(np.array(h_st10))
            cdf_10 = np.arange(1, len(sorted_h_10) + 1) / float(len(sorted_h_10))
            ax.plot(sorted_h_10, cdf_10 * 100.0, '--', color='#377eb8', lw=2.0, label='Stage 10/11 Baseline (%d elems)' % len(stage10_records))
            
        ax.set_xlabel('Element Size $h_{\\mathrm{eq}}$ [$\\mu$m]')
        ax.set_ylabel('Cumulative Distribution [%]')
        ax.set_title('(b) Element Size CDF Comparison')
        ax.grid(True, ls=':', alpha=0.6)
        ax.legend(loc='lower right')
        
        # Panel C: Corridor vs Far-Field Element Count
        ax = axes[1, 0]
        n_corr = sum(1 for r in adapt_records if 0.45 <= r['cy'] <= 0.55)
        n_far = n_ad - n_corr
        
        labels = ['Crack Corridor\n($|y-0.5| \\leq 0.05$)', 'Far-Field\n($|y-0.5| > 0.05$)']
        counts = [n_corr, n_far]
        percentages = [n_corr * 100.0 / n_ad, n_far * 100.0 / n_ad]
        
        bars = ax.bar(labels, counts, color=['#d95f02', '#7570b3'], edgecolor='black', width=0.5)
        for b, p, c in zip(bars, percentages, counts):
            ax.text(b.get_x() + b.get_width()/2.0, b.get_height() + 1500, '%d\n(%.1f%%)' % (c, p), ha='center', va='bottom', fontweight='bold')
        ax.set_ylim(0, max(counts) + 18000)
        ax.set_ylabel('Element Count')
        ax.set_title('(c) Spatial Partition of Adapted Elements')
        ax.grid(axis='y', ls=':', alpha=0.6)
        
        # Panel D: Refinement Band Width w(x) Comparison
        ax = axes[1, 1]
        x_slices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        w_st12 = []
        for xs in x_slices:
            sl = [r['cy'] for r in adapt_records if abs(r['cx'] - xs) <= 0.03 and r['h_eq'] <= 0.005]
            w_st12.append(max(sl) - min(sl) if sl else 0.0)
            
        ax.plot(x_slices, w_st12, 'o-', color='#e41a1c', lw=2.2, ms=6, label='Stage 12 Non-Uniform Refined Zone')
        # Target published band
        ax.axhline(0.10, color='green', ls='--', lw=2.0, label='Pandey & Kumar Target ($w \\approx 0.10$ mm)')
        ax.fill_between([0.0, 1.0], 0.08, 0.12, color='green', alpha=0.15)
        
        ax.set_xlim(0.05, 0.95)
        ax.set_ylim(0.0, 1.05)
        ax.set_xlabel('X Coordinate [mm]')
        ax.set_ylabel('Refined Band Width $w(x)$ [mm] ($h \\leq 5\\mu$m)')
        ax.set_title('(d) Refined Corridor Width Across Domain')
        ax.grid(True, ls=':', alpha=0.6)
        ax.legend(loc='upper right')
        
        plt.tight_layout()
        f3_png = os.path.join(figures_dir, "mode1_stage12_fig3_adapted_morphology_comparison.png")
        f3_pdf = os.path.join(figures_dir, "mode1_stage12_fig3_adapted_morphology_comparison.pdf")
        plt.savefig(f3_png, dpi=300)
        plt.savefig(f3_pdf)
        plt.close()
        print("Figure 3 saved: %s" % f3_png)
        
    print("Stage 12 Figures generation complete!")

if __name__ == "__main__":
    res_d = "models/pandey_kumar_mode1/98_mode1_stage12_nonuniform_coarse_diagnostic"
    fig_d = "results/figures/mode1_gate6b"
    generate_stage12_figures(res_d, fig_d)
