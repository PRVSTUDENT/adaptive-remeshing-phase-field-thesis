import os
import sys
import traceback

log_file = r"C:\Users\pruth\.gemini\antigravity-cli\brain\7f2a7209-1728-47f5-ad87-7c80b6d0d256\plot_log.txt"

with open(log_file, "w", encoding="utf-8") as log:
    try:
        import csv
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        plt.rcParams.update({
            'font.size': 11,
            'font.family': 'serif',
            'axes.labelsize': 12,
            'axes.titlesize': 13,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 14,
            'lines.linewidth': 1.8,
            'grid.alpha': 0.5,
            'grid.linestyle': '--'
        })

        workspace = r"D:\Master thesis\Adaptive remeshing"
        figures_dir = os.path.join(workspace, "docs", "MA_AdaptiveRemeshing_Report_2026_main", "figures")
        os.makedirs(figures_dir, exist_ok=True)
        results_figures_dir = os.path.join(workspace, "results", "figures", "mode1_gate6b")
        os.makedirs(results_figures_dir, exist_ok=True)

        # 1. Load Fixed Ref Data
        ref_csv = os.path.join(workspace, "models", "pandey_kumar_mode1", "gate6b_claims_and_matched_audit", "history_S1_1409734.mmaster02.csv")
        ref_u, ref_f, ref_w, ref_efrac, ref_eelas, ref_emodel = [], [], [], [], [], []
        if os.path.exists(ref_csv):
            with open(ref_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ref_u.append(float(row['u_mm']))
                    ref_f.append(float(row['force_kN']))
                    ref_w.append(float(row['w_ext_mJ']))
                    ref_efrac.append(float(row['e_frac_mJ']))
                    ref_eelas.append(float(row['e_elas_mJ']))
                    ref_emodel.append(float(row['e_model_mJ']))
            log.write(f"Loaded {len(ref_u)} ref points\n")

        # 2. Load ET1 Adaptive Baseline
        et1_csv = os.path.join(workspace, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv")
        et1_u, et1_f, et1_w = [], [], []
        if os.path.exists(et1_csv):
            with open(et1_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    et1_u.append(float(row['displacement_mm']))
                    et1_f.append(float(row['reaction_force_kN']))
                    et1_w.append(float(row['w_ext_mJ']))
            log.write(f"Loaded {len(et1_u)} ET1 points\n")

        # 3. Load ET3 Data
        et3_csv = os.path.join(workspace, "models", "pandey_kumar_mode1", "35_stage14_step2_adaptive_candidate_et3_5k", "PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE_fu.csv")
        et3_u, et3_f, et3_w, et3_efrac, et3_eelas, et3_emodel = [], [], [], [], [], []
        if os.path.exists(et3_csv):
            with open(et3_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    et3_u.append(float(row.get('Displacement_mm') or row.get('displacement_mm')))
                    et3_f.append(float(row.get('ReactionForce_kN') or row.get('reaction_force_kN')))
                    et3_w.append(float(row.get('ExternalWork_mJ') or row.get('w_ext_mJ')))
                    et3_efrac.append(float(row.get('FractureEnergy_mJ') or row.get('e_frac_mJ')))
                    et3_eelas.append(float(row.get('ElasticEnergy_mJ') or row.get('e_elas_mJ')))
                    et3_emodel.append(float(row.get('TotalModelEnergy_mJ') or row.get('e_model_mJ')))
            log.write(f"Loaded {len(et3_u)} ET3 points\n")

        # 4. Load ET5 Data
        et5_csv = os.path.join(workspace, "models", "pandey_kumar_mode1", "36_stage14_step2_adaptive_candidate_et5_4k", "PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE_fu.csv")
        et5_u, et5_f, et5_w, et5_efrac, et5_eelas, et5_emodel = [], [], [], [], [], []
        if os.path.exists(et5_csv):
            with open(et5_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    et5_u.append(float(row.get('Displacement_mm') or row.get('displacement_mm')))
                    et5_f.append(float(row.get('ReactionForce_kN') or row.get('reaction_force_kN')))
                    et5_w.append(float(row.get('ExternalWork_mJ') or row.get('w_ext_mJ')))
                    et5_efrac.append(float(row.get('FractureEnergy_mJ') or row.get('e_frac_mJ')))
                    et5_eelas.append(float(row.get('ElasticEnergy_mJ') or row.get('e_elas_mJ')))
                    et5_emodel.append(float(row.get('TotalModelEnergy_mJ') or row.get('e_model_mJ')))
            log.write(f"Loaded {len(et5_u)} ET5 points\n")

        # FIGURE 1: Reaction Force vs Displacement
        fig, ax = plt.subplots(figsize=(8, 5.5))
        ax.plot(ref_u, ref_f, color='black', linestyle='-', label=r'Fixed Reference (15,192 FE, $F_{\max}=0.758$ kN)')
        ax.plot(et1_u, et1_f, color='#1f77b4', linestyle='--', label=r'ET1 Baseline (14,483 FE, $F_{\max}=0.744$ kN, $u_{\rm term}=0.0079$)')
        ax.plot(et3_u, et3_f, color='#2ca02c', linestyle='-.', label=r'ET3 Adaptive (5,189 FE, $F_{\max}=0.759$ kN, $u_{\rm term}=0.0100$)')
        ax.plot(et5_u, et5_f, color='#d62728', linestyle=':', label=r'ET5 Adaptive (4,692 FE, $F_{\max}=0.765$ kN, $u_{\rm term}=0.0100$)')

        ax.set_xlabel('Prescribed Displacement $u$ [mm]')
        ax.set_ylabel('Reaction Force $F$ [kN]')
        ax.set_title('Mode-I Stage-14 Step-2 ErrorTarget Sensitivity: Force-Displacement Response')
        ax.grid(True)
        ax.legend(loc='upper right', framealpha=0.9)
        ax.set_xlim([0.0, 0.0102])
        ax.set_ylim([0.0, 0.85])

        for out_dir in [figures_dir, results_figures_dir]:
            fig.savefig(os.path.join(out_dir, "fig_mode1_gate6b_step2_fu_comparison.pdf"), bbox_inches='tight', dpi=300)
            fig.savefig(os.path.join(out_dir, "fig_mode1_gate6b_step2_fu_comparison.png"), bbox_inches='tight', dpi=300)
        plt.close(fig)
        log.write("Saved Figure 1\n")

        # FIGURE 2: Global Energy Components
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

        ax1.plot(ref_u, ref_w, 'k-', label=r'Ref $W_{\rm ext}$')
        ax1.plot(ref_u, ref_efrac, 'k--', label=r'Ref $\mathcal{E}_{\rm frac}$')
        ax1.plot(et3_u, et3_w, color='#2ca02c', linestyle='-', label=r'ET3 $W_{\rm ext}$')
        ax1.plot(et3_u, et3_efrac, color='#2ca02c', linestyle='--', label=r'ET3 $\mathcal{E}_{\rm frac}$')
        ax1.plot(et5_u, et5_w, color='#d62728', linestyle='-', label=r'ET5 $W_{\rm ext}$')
        ax1.plot(et5_u, et5_efrac, color='#d62728', linestyle='--', label=r'ET5 $\mathcal{E}_{\rm frac}$')

        ax1.set_xlabel('Prescribed Displacement $u$ [mm]')
        ax1.set_ylabel('Energy [mJ]')
        ax1.set_title('External Work & Implemented Fracture Energy')
        ax1.grid(True)
        ax1.legend(loc='upper left', framealpha=0.9)
        ax1.set_xlim([0.0, 0.0102])

        et3_delta = [w - em for w, em in zip(et3_w, et3_emodel)]
        et5_delta = [w - em for w, em in zip(et5_w, et5_emodel)]
        ref_delta = [w - em for w, em in zip(ref_w, ref_emodel)]

        ax2.plot(ref_u, ref_delta, 'k-', label=r'Ref $\Delta_{\rm book}$ (0.76% rel)')
        ax2.plot(et3_u, et3_delta, color='#2ca02c', linestyle='-', label=r'ET3 $\Delta_{\rm book}$ (11.04% rel)')
        ax2.plot(et5_u, et5_delta, color='#d62728', linestyle='-', label=r'ET5 $\Delta_{\rm book}$ (12.10% rel)')

        ax2.set_xlabel('Prescribed Displacement $u$ [mm]')
        ax2.set_ylabel(r'Bookkeeping Discrepancy $\Delta_{\rm book}$ [mJ]')
        ax2.set_title(r'Energy Balance Discrepancy ($\Delta_{\rm book} = W_{\rm ext} - \mathcal{E}_{\rm model}$)')
        ax2.grid(True)
        ax2.legend(loc='upper left', framealpha=0.9)
        ax2.set_xlim([0.0, 0.0102])

        plt.tight_layout()
        for out_dir in [figures_dir, results_figures_dir]:
            fig.savefig(os.path.join(out_dir, "fig_mode1_gate6b_step2_energy_balance.pdf"), bbox_inches='tight', dpi=300)
            fig.savefig(os.path.join(out_dir, "fig_mode1_gate6b_step2_energy_balance.png"), bbox_inches='tight', dpi=300)
        plt.close(fig)
        log.write("Saved Figure 2\n")

        # FIGURE 3: Ligament Damage Profiles
        et3_prof_csv = os.path.join(workspace, "models", "pandey_kumar_mode1", "35_stage14_step2_adaptive_candidate_et3_5k", "PK_MODE1_STAGE14_STEP2_ET3_5K_ligament_profiles.csv")
        et5_prof_csv = os.path.join(workspace, "models", "pandey_kumar_mode1", "36_stage14_step2_adaptive_candidate_et5_4k", "PK_MODE1_STAGE14_STEP2_ET5_4K_ligament_profiles.csv")

        if os.path.exists(et3_prof_csv) and os.path.exists(et5_prof_csv):
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
            
            et3_profs = {}
            with open(et3_prof_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u_t = float(row.get('u_target_mm') or row.get('target_u_mm'))
                    if u_t not in et3_profs:
                        et3_profs[u_t] = {'x': [], 'd': []}
                    et3_profs[u_t]['x'].append(float(row.get('x_mm') or row.get('x_coord_mm')))
                    et3_profs[u_t]['d'].append(float(row.get('d') or row.get('damage_d')))
                    
            et5_profs = {}
            with open(et5_prof_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u_t = float(row.get('u_target_mm') or row.get('target_u_mm'))
                    if u_t not in et5_profs:
                        et5_profs[u_t] = {'x': [], 'd': []}
                    et5_profs[u_t]['x'].append(float(row.get('x_mm') or row.get('x_coord_mm')))
                    et5_profs[u_t]['d'].append(float(row.get('d') or row.get('damage_d')))
                    
            sel_u = [0.0050, 0.005857, 0.0065, 0.0070, 0.0100]
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for u_val, col in zip(sel_u, colors):
                for k in et3_profs:
                    if abs(k - u_val) < 1e-4:
                        pts = sorted(zip(et3_profs[k]['x'], et3_profs[k]['d']))
                        xs = [p[0] for p in pts]
                        ds = [p[1] for p in pts]
                        ax1.plot(xs, ds, color=col, label=f'$u = {u_val:.4f}$ mm')
                        break
                        
                for k in et5_profs:
                    if abs(k - u_val) < 1e-4:
                        pts = sorted(zip(et5_profs[k]['x'], et5_profs[k]['d']))
                        xs = [p[0] for p in pts]
                        ds = [p[1] for p in pts]
                        ax2.plot(xs, ds, color=col, label=f'$u = {u_val:.4f}$ mm')
                        break

            ax1.set_xlabel('Ligament Coordinate $x$ [mm] (at $y=0.50$ mm)')
            ax1.set_ylabel('Phase-Field Damage $d$')
            ax1.set_title('ET3 Adaptive Candidate (5,189 FE)')
            ax1.grid(True)
            ax1.legend(loc='upper left', framealpha=0.9)
            ax1.set_xlim([0.48, 1.02])
            ax1.set_ylim([-0.05, 1.05])
            
            ax2.set_xlabel('Ligament Coordinate $x$ [mm] (at $y=0.50$ mm)')
            ax2.set_title('ET5 Adaptive Candidate (4,692 FE)')
            ax2.grid(True)
            ax2.legend(loc='upper left', framealpha=0.9)
            ax2.set_xlim([0.48, 1.02])
            
            plt.tight_layout()
            for out_dir in [figures_dir, results_figures_dir]:
                fig.savefig(os.path.join(out_dir, "fig_mode1_gate6b_step2_ligament_damage_profiles.pdf"), bbox_inches='tight', dpi=300)
                fig.savefig(os.path.join(out_dir, "fig_mode1_gate6b_step2_ligament_damage_profiles.png"), bbox_inches='tight', dpi=300)
            plt.close(fig)
            log.write("Saved Figure 3\n")
            
        log.write("ALL FIGURES GENERATED SUCCESSFULLY\n")
    except Exception as e:
        log.write(f"EXCEPTION: {str(e)}\n")
        log.write(traceback.format_exc())
