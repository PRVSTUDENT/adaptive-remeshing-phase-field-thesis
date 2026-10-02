"""
Standalone convergence comparison script for Gate 1: Job 1401091 (Harmonized Isotropic) vs Job 1401159 (Harmonized Spectral).
Extracts matched displacement frames, iteration histories, and cutback sequences.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def parse_sta(sta_path):
    records = []
    with open(sta_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 9:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    num_att = int(parts[2])
                    sev_iter = int(parts[3])
                    eq_iter = int(parts[4])
                    tot_iter = int(parts[5])
                    tot_time = float(parts[6])
                    step_time = float(parts[7])
                    inc_time = float(parts[8])
                    records.append({
                        'step': step,
                        'increment': inc,
                        'attempts': num_att,
                        'sev_iter': sev_iter,
                        'eq_iter': eq_iter,
                        'iterations': tot_iter,
                        'tot_time': tot_time,
                        'step_time': step_time,
                        'inc_time': inc_time
                    })
                except (ValueError, IndexError):
                    continue
    return pd.DataFrame(records)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))

    iso_fu_path = os.path.join(project_root, "results", "pandey_kumar_mode1", "gate1_harmonized", "job_1401091_fu.csv")
    spec_fu_path = os.path.join(project_root, "results", "pandey_kumar_mode1", "gate1_spectral", "job_1401159_fu.csv")
    iso_sta_path = os.path.join(project_root, "models", "pandey_kumar_mode1", "01_standard_pfm_bvp_harmonized", "PK_MODE1_STANDARD_PFM.sta")
    spec_sta_path = os.path.join(project_root, "models", "pandey_kumar_mode1", "01_standard_pfm_bvp_spectral", "PK_MODE1_STANDARD_PFM.sta")

    # Fallback to local paths if needed
    if not os.path.exists(spec_sta_path):
        spec_sta_path = os.path.join(base_dir, "PK_MODE1_STANDARD_PFM.sta")

    df_iso = pd.read_csv(iso_fu_path)
    df_spec = pd.read_csv(spec_fu_path)

    df_iso_s2 = df_iso[df_iso['step'] == 2].copy().reset_index(drop=True)
    df_spec_s2 = df_spec[df_spec['step'] == 2].copy().reset_index(drop=True)

    df_iso_sta = parse_sta(iso_sta_path)
    df_spec_sta = parse_sta(spec_sta_path)

    merged_iso = pd.merge(df_iso_s2, df_iso_sta[df_iso_sta['step'] == 2], on=['step', 'increment'], how='left')
    merged_spec = pd.merge(df_spec_s2, df_spec_sta[df_spec_sta['step'] == 2], on=['step', 'increment'], how='left')

    target_u_values = [
        0.0050, 0.0052, 0.0054, 0.0055, 0.0056, 0.0058, 0.0060, 
        0.00605, 0.006072, 0.006098, 0.006105, 0.006109, 0.006111
    ]

    matched_records = []
    for tu in target_u_values:
        idx_iso = (merged_iso['u_mm'] - tu).abs().idxmin()
        row_iso = merged_iso.iloc[idx_iso]
        
        idx_spec = (merged_spec['u_mm'] - tu).abs().idxmin()
        row_spec = merged_spec.iloc[idx_spec]
        
        matched_records.append({
            'target_u_mm': tu,
            'iso_inc': int(row_iso['increment']),
            'iso_u_mm': row_iso['u_mm'],
            'iso_F_kN': row_iso['F_kN'],
            'iso_iters': int(row_iso['iterations']) if pd.notnull(row_iso['iterations']) else np.nan,
            'iso_dt': row_iso['inc_time'] if pd.notnull(row_iso['inc_time']) else np.nan,
            'spec_inc': int(row_spec['increment']),
            'spec_u_mm': row_spec['u_mm'],
            'spec_F_kN': row_spec['F_kN'],
            'spec_iters': int(row_spec['iterations']) if pd.notnull(row_spec['iterations']) else np.nan,
            'spec_dt': row_spec['inc_time'] if pd.notnull(row_spec['inc_time']) else np.nan,
            'delta_F_kN': row_spec['F_kN'] - row_iso['F_kN'],
            'delta_F_pct': ((row_spec['F_kN'] - row_iso['F_kN']) / row_iso['F_kN']) * 100.0
        })

    df_matched = pd.DataFrame(matched_records)
    out_csv = os.path.join(base_dir, "job_1401091_vs_1401159_matched_displacement_comparison.csv")
    df_matched.to_csv(out_csv, index=False)
    print("Saved matched displacement table to:", out_csv)

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9), sharex=True)

    ax1.plot(merged_iso['u_mm'], merged_iso['F_kN'], 'b-', label='Job 1401091 (Harmonized Isotropic, Free Top)', linewidth=1.8)
    ax1.plot(merged_spec['u_mm'], merged_spec['F_kN'], 'r--', label='Job 1401159 (Harmonized Spectral Split, Free Top)', linewidth=2.0)
    ax1.axvline(x=0.006072, color='blue', linestyle=':', alpha=0.7, label='Isotropic Peak ($u=0.006072$ mm, $F=0.7650$ kN)')
    ax1.axvline(x=0.006098, color='red', linestyle=':', alpha=0.7, label='Spectral Peak ($u=0.006098$ mm, $F=0.7771$ kN)')
    ax1.axvline(x=0.006111, color='darkred', linestyle='-', alpha=0.9, label='Spectral Cutback Stall ($u=0.006111$ mm)')
    ax1.set_ylabel('Reaction Force $F$ [kN]', fontsize=11)
    ax1.set_title('Mode-I Standard PFM: Isotropic vs Spectral Pre-Peak & Early Softening Comparison', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', frameon=True, fontsize=9)
    ax1.set_xlim(0.0050, 0.0062)
    ax1.set_ylim(0.65, 0.80)

    ax2.plot(merged_iso['u_mm'], merged_iso['iterations'], 'b.-', label='Isotropic (Job 1401091) Iterations / Inc', markersize=3, alpha=0.7)
    ax2.plot(merged_spec['u_mm'], merged_spec['iterations'], 'r.-', label='Spectral (Job 1401159) Iterations / Inc', markersize=4, alpha=0.8)
    ax2.set_xlabel('Prescribed Displacement $u$ [mm]', fontsize=11)
    ax2.set_ylabel('Iterations per Increment', fontsize=11)
    ax2.set_title(r'Newton-Raphson Iteration Count Evolution ($u \in [0.0050, 0.0062]$ mm)', fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', frameon=True, fontsize=9)
    ax2.set_ylim(0, 16)

    plt.tight_layout()
    out_png = os.path.join(base_dir, "job_1401091_vs_1401159_iteration_and_fu_comparison.png")
    plt.savefig(out_png, dpi=300)
    print("Saved comparison plot to:", out_png)

if __name__ == '__main__':
    main()
