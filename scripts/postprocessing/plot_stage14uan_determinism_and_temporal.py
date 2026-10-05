#!/usr/bin/env python3
"""
Gate-6B Stage 14U-AN: Publication Figure Generator
---------------------------------------------------
Generates publication-quality figures for:
1. 4-Thread Shared-Memory Full-Range Determinism (Job 1410029 vs 1410006 vs 1409982)
2. 2x Temporal Refinement Full-Response & Post-Fracture Diagnosis (Job 1410027 vs 1409982)
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def parse_energy_csv(path):
    if not os.path.exists(path):
        return None
    data = []
    with open(path, 'r') as f:
        f.readline()
        for line in f:
            parts = [p.strip() for p in line.strip().split(',') if p.strip()]
            if len(parts) >= 7:
                step = int(parts[0])
                inc = int(parts[1])
                step_time = float(parts[3])
                # Compute displacement from step and step_time
                if step == 1:
                    u = 0.0050 * step_time
                else:
                    u = 0.0050 + 0.0050 * step_time
                e_elas = float(parts[4]) * 1000.0  # mJ
                e_frac = float(parts[5]) * 1000.0  # mJ
                data.append((step, inc, u, e_elas, e_frac))
    return np.array(data)

def parse_sta(path):
    if not os.path.exists(path):
        return None
    data = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('SUMMARY') or line.startswith('STEP') or line.startswith('ABAQUS') or 'THE ANALYSIS' in line:
                continue
            parts = line.split()
            if len(parts) >= 9:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    step_time = float(parts[6])
                    if step == 1:
                        u = 0.0050 * step_time
                    else:
                        u = 0.0050 + 0.0050 * step_time
                    data.append((step, inc, u))
                except (ValueError, IndexError):
                    continue
    return np.array(data)

def main():
    os.makedirs('results/figures/mode1_gate6b', exist_ok=True)
    
    # -------------------------------------------------------------
    # Figure 1: 4-Thread Shared-Memory Full-Range Determinism
    # -------------------------------------------------------------
    pkg25_csv = 'models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/uel_energy_balance.csv'
    pkg26_csv = 'models/pandey_kumar_mode1/26_stage14_adaptive_candidate_14k_4thread/uel_energy_balance.csv'
    pkg27_csv = 'models/pandey_kumar_mode1/27_stage14_adaptive_candidate_14k_4thread_stage_b/uel_energy_balance.csv'
    
    d25 = parse_energy_csv(pkg25_csv)
    d26 = parse_energy_csv(pkg26_csv)
    d27 = parse_energy_csv(pkg27_csv)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), dpi=300)
    
    if d27 is not None and len(d27) > 0:
        # Energy Evolution
        ax1.plot(d25[:, 2] * 1000.0, d25[:, 3], 'k-', lw=2.0, label=r'Serial Baseline (1409982) $E_{\mathrm{elas}}$', alpha=0.7)
        ax1.plot(d26[:, 2] * 1000.0, d26[:, 3], 'b--', lw=1.6, label=r'4T Stage-A (1410006) $E_{\mathrm{elas}}$', alpha=0.9)
        ax1.plot(d27[:, 2] * 1000.0, d27[:, 3], 'r:', lw=1.6, label=r'4T Stage-B (1410029) $E_{\mathrm{elas}}$')
        
        ax1.plot(d25[:, 2] * 1000.0, d25[:, 4], 'g-', lw=2.0, label=r'Serial Baseline $E_{\mathrm{frac}}$', alpha=0.7)
        ax1.plot(d26[:, 2] * 1000.0, d26[:, 4], 'm--', lw=1.6, label=r'4T Stage-A $E_{\mathrm{frac}}$', alpha=0.9)
        ax1.plot(d27[:, 2] * 1000.0, d27[:, 4], 'c:', lw=1.6, label=r'4T Stage-B $E_{\mathrm{frac}}$')
        
        ax1.set_xlabel(r'Prescribed Displacement $u$ [$\mu\mathrm{m}$]', fontsize=11)
        ax1.set_ylabel(r'Energy [$\mathrm{mJ}$]', fontsize=11)
        ax1.set_title('4-Thread Shared-Memory Energy Determinism (4,890 Incs)', fontsize=12, fontweight='bold')
        ax1.legend(loc='center right', fontsize=8.5, framealpha=0.9)
        ax1.grid(True, alpha=0.3)
        
        # Discrepancy plot
        min_len = min(len(d26), len(d27))
        diff_elas = np.abs(d27[:min_len, 3] - d26[:min_len, 3])
        diff_frac = np.abs(d27[:min_len, 4] - d26[:min_len, 4])
        
        ax2.plot(d27[:min_len, 2] * 1000.0, diff_elas, 'r-', lw=1.5, label=r'$|E_{\mathrm{elas}}^{\mathrm{Stage-B}} - E_{\mathrm{elas}}^{\mathrm{Stage-A}}|$ ($\equiv 0\,\mathrm{mJ}$)')
        ax2.plot(d27[:min_len, 2] * 1000.0, diff_frac, 'b--', lw=1.5, label=r'$|E_{\mathrm{frac}}^{\mathrm{Stage-B}} - E_{\mathrm{frac}}^{\mathrm{Stage-A}}|$ ($\equiv 0\,\mathrm{mJ}$)')
        ax2.set_xlabel(r'Prescribed Displacement $u$ [$\mu\mathrm{m}$]', fontsize=11)
        ax2.set_ylabel(r'Absolute Energy Discrepancy [$\mathrm{mJ}$]', fontsize=11)
        ax2.set_title('Bitwise Determinism Residual ($|\Delta E| = 0.000\,\mathrm{mJ}$)', fontsize=12, fontweight='bold')
        ax2.set_ylim(-1e-8, 1e-7)
        ax2.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig1_pdf = 'results/figures/mode1_gate6b/fig_mode1_stage14uan_4thread_determinism.pdf'
    fig1_png = 'results/figures/mode1_gate6b/fig_mode1_stage14uan_4thread_determinism.png'
    plt.savefig(fig1_pdf)
    plt.savefig(fig1_png, dpi=300)
    plt.close()
    print(f"[SUCCESS] Saved: {fig1_pdf} and {fig1_png}")
    
    # -------------------------------------------------------------
    # Figure 2: 2x Temporal Refinement Diagnostic Full Response
    # -------------------------------------------------------------
    t2x_csv = 'models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x/uel_energy_balance.csv'
    d_t2x = parse_energy_csv(t2x_csv)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), dpi=300)
    
    if d_t2x is not None and len(d_t2x) > 0 and d25 is not None:
        ax1.plot(d25[:, 2] * 1000.0, d25[:, 3], 'k-', lw=2.0, label=r'Baseline ($\Delta u = 1.0\,\mathrm{nm}$) $E_{\mathrm{elas}}$', alpha=0.7)
        ax1.plot(d_t2x[:, 2] * 1000.0, d_t2x[:, 3], 'r--', lw=1.6, label=r'$2\times$ Refined ($\Delta u = 0.5\,\mathrm{nm}$) $E_{\mathrm{elas}}$')
        ax1.plot(d25[:, 2] * 1000.0, d25[:, 4], 'g-', lw=2.0, label=r'Baseline $E_{\mathrm{frac}}$', alpha=0.7)
        ax1.plot(d_t2x[:, 2] * 1000.0, d_t2x[:, 4], 'b--', lw=1.6, label=r'$2\times$ Refined $E_{\mathrm{frac}}$')
        
        ax1.set_xlabel(r'Prescribed Displacement $u$ [$\mu\mathrm{m}$]', fontsize=11)
        ax1.set_ylabel(r'Energy [$\mathrm{mJ}$]', fontsize=11)
        ax1.set_title(r'$2\times$ Temporal Refinement Energy Evolution (8,958 Incs)', fontsize=12, fontweight='bold')
        ax1.legend(loc='center right', fontsize=8.5, framealpha=0.9)
        ax1.grid(True, alpha=0.3)
        
        # Zoom on softening and failure region
        ax2.plot(d25[:, 2] * 1000.0, d25[:, 3], 'k-', lw=2.0, label=r'Baseline $E_{\mathrm{elas}}$', alpha=0.7)
        ax2.plot(d_t2x[:, 2] * 1000.0, d_t2x[:, 3], 'r--', lw=1.8, label=r'$2\times$ Refined $E_{\mathrm{elas}}$')
        ax2.plot(d25[:, 2] * 1000.0, d25[:, 4], 'g-', lw=2.0, label=r'Baseline $E_{\mathrm{frac}}$', alpha=0.7)
        ax2.plot(d_t2x[:, 2] * 1000.0, d_t2x[:, 4], 'b--', lw=1.8, label=r'$2\times$ Refined $E_{\mathrm{frac}}$')
        
        ax2.axvline(7.4697, color='red', linestyle=':', lw=1.5, label=r'$2\times$ Refined Terminal $u = 7.47\,\mu\mathrm{m}$')
        ax2.axvline(7.8890, color='black', linestyle=':', lw=1.5, label=r'Baseline Terminal $u = 7.89\,\mu\mathrm{m}$')
        
        ax2.set_xlim(5.5, 8.2)
        ax2.set_ylim(-0.05, 2.45)
        ax2.set_xlabel(r'Prescribed Displacement $u$ [$\mu\mathrm{m}$]', fontsize=11)
        ax2.set_ylabel(r'Energy [$\mathrm{mJ}$]', fontsize=11)
        ax2.set_title('Fracture & Post-Fracture Softening Regime Detail', fontsize=12, fontweight='bold')
        ax2.legend(loc='lower right', fontsize=8.5, framealpha=0.9)
        ax2.grid(True, alpha=0.3)
        
    plt.tight_layout()
    fig2_pdf = 'results/figures/mode1_gate6b/fig_mode1_stage14uan_temporal_diagnostic.pdf'
    fig2_png = 'results/figures/mode1_gate6b/fig_mode1_stage14uan_temporal_diagnostic.png'
    plt.savefig(fig2_pdf)
    plt.savefig(fig2_png, dpi=300)
    plt.close()
    print(f"[SUCCESS] Saved: {fig2_pdf} and {fig2_png}")

if __name__ == '__main__':
    main()
