import sys
import os
import json
from odbAccess import openOdb, NODAL, INTEGRATION_POINT

def run():
    workdir = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/batch_mode1_energy_convergence/S1_h0030_15k_diagnostic_r2"
    odb_path = os.path.join(workdir, "PK_M1_S1_DIAG_R2.odb")
    out_json = os.path.join(workdir, "CANONICAL_S1_1406839_REHARVEST.json")
    
    print("==================================================================")
    print("AUTHORITATIVE CANONICAL ODB HARVEST: Job 1406839.mmaster02")
    print("ODB: " + str(odb_path))
    print("==================================================================")
    
    odb = openOdb(odb_path, readOnly=True)
    inst = odb.rootAssembly.instances['PART-1-1']
    
    total_elements = len(inst.elements)
    total_nodes = len(inst.nodes)
    print("Total Assembly Elements: " + str(total_elements))
    print("Total Assembly Nodes:    " + str(total_nodes))
    
    vis_elset = inst.elementSets['UMATELEM'] if 'UMATELEM' in inst.elementSets else inst.elementSets['ALL_ELEM']
    rp_nset = inst.nodeSets['N_RP']
    bottom_nset = inst.nodeSets['N_BOTTOM']
    
    step1 = odb.steps['Step-1']
    step2 = odb.steps['Step-2']
    n_f1 = len(step1.frames)
    n_f2 = len(step2.frames)
    print("Converged Frames: Step-1 = " + str(n_f1) + ", Step-2 = " + str(n_f2) + " (Total = " + str(n_f1 + n_f2) + ")")
    
    all_time = []
    all_u = []
    all_f_rp = []
    
    for f_idx in range(n_f1):
        frame = step1.frames[f_idx]
        t = frame.frameValue
        u_sub = frame.fieldOutputs['U'].getSubset(position=NODAL, region=rp_nset)
        rf_sub = frame.fieldOutputs['RF'].getSubset(position=NODAL, region=rp_nset)
        u_val = u_sub.values[0].data[1] if len(u_sub.values) > 0 else 0.0
        f_rp = rf_sub.values[0].data[1] if len(rf_sub.values) > 0 else 0.0
        all_time.append(t)
        all_u.append(u_val)
        all_f_rp.append(f_rp)
        
    for f_idx in range(n_f2):
        frame = step2.frames[f_idx]
        t = frame.frameValue
        u_sub = frame.fieldOutputs['U'].getSubset(position=NODAL, region=rp_nset)
        rf_sub = frame.fieldOutputs['RF'].getSubset(position=NODAL, region=rp_nset)
        u_val = u_sub.values[0].data[1] if len(u_sub.values) > 0 else 0.0
        f_rp = rf_sub.values[0].data[1] if len(rf_sub.values) > 0 else 0.0
        all_time.append(1.0 + t)
        all_u.append(u_val)
        all_f_rp.append(f_rp)
        
    total_pts = len(all_u)
    print("Extracted " + str(total_pts) + " continuous true nodal F-u points.")
    
    # Cumulative work
    all_w = [0.0]
    cum_w = 0.0
    for i in range(1, total_pts):
        du = all_u[i] - all_u[i-1]
        if du > 1e-15:
            dw = 0.5 * (all_f_rp[i] + all_f_rp[i-1]) * du
            cum_w += dw
        all_w.append(cum_w)
        
    w_ext_trap = cum_w
    
    # Left and right Riemann
    w_left = 0.0
    w_right = 0.0
    for i in range(1, total_pts):
        du = all_u[i] - all_u[i-1]
        w_left += all_f_rp[i-1] * du
        w_right += all_f_rp[i] * du
        
    # Sample targets
    sample_targets = [
        ('Step-1', 0),
        ('Step-1', 200),
        ('Step-1', 400),
        ('Step-1', 1000),
        ('Step-1', 2000),
        ('Step-2', 0),
        ('Step-2', 500),
        ('Step-2', 856),
        ('Step-2', 1000),
        ('Step-2', 2000),
        ('Step-2', 3000),
        ('Step-2', 4000),
        ('Step-2', 4994),
        ('Step-2', 5000)
    ]
    
    sample_records = []
    
    print("\n--- SAMPLE FRAME FIELD AUDIT ---")
    for sname, f_idx in sample_targets:
        step = odb.steps[sname]
        if f_idx >= len(step.frames):
            continue
        frame = step.frames[f_idx]
        g_idx = f_idx if sname == 'Step-1' else (n_f1 + f_idx)
        t_val = all_time[g_idx]
        u_val = all_u[g_idx]
        f_rp = all_f_rp[g_idx]
        w_val = all_w[g_idx]
        
        rf_bottom_sub = frame.fieldOutputs['RF'].getSubset(position=NODAL, region=bottom_nset)
        sum_rf_bottom = sum(v.data[1] for v in rf_bottom_sub.values)
        eq_residual = f_rp + sum_rf_bottom
        
        sdv17_sub = frame.fieldOutputs['SDV17'].getSubset(position=INTEGRATION_POINT, region=vis_elset)
        sdv18_sub = frame.fieldOutputs['SDV18'].getSubset(position=INTEGRATION_POINT, region=vis_elset)
        
        sum_sdv17 = 0.0
        vis_elem_count_17 = 0
        for v in sdv17_sub.values:
            if v.integrationPoint == 1 or v.integrationPoint is None:
                sum_sdv17 += v.data
                vis_elem_count_17 += 1
                
        sum_sdv18 = 0.0
        vis_elem_count_18 = 0
        for v in sdv18_sub.values:
            if v.integrationPoint == 1 or v.integrationPoint is None:
                sum_sdv18 += v.data
                vis_elem_count_18 += 1
                
        r_book = w_val - (sum_sdv18 + sum_sdv17)
        rel_diff = (r_book / w_val * 100.0) if w_val > 1e-12 else 0.0
        
        rec = {
            'step': sname,
            'frame_idx': int(f_idx),
            'global_idx': int(g_idx),
            'time': float(t_val),
            'disp_u_mm': float(u_val),
            'force_RF2_RP_kN': float(f_rp),
            'sum_RF2_bottom_kN': float(sum_rf_bottom),
            'eq_residual_kN': float(eq_residual),
            'W_ext_trap_kN_mm': float(w_val),
            'E_elas_kN_mm': float(sum_sdv18),
            'E_frac_kN_mm': float(sum_sdv17),
            'R_bookkeeping_kN_mm': float(r_book),
            'rel_diff_pct': float(rel_diff),
            'n_unique_vis_elements': int(vis_elem_count_18)
        }
        sample_records.append(rec)
        print("%s Frame %4d | u=%.6f mm | F_RP=%.6f kN, F_Bot=%.6f kN, EqRes=%.2e | W=%.6e, E_elas=%.6e, E_frac=%.6e | R_book=%.6e (%.3f %%) | Vis=%d" % (
            sname, f_idx, u_val, f_rp, sum_rf_bottom, eq_residual, w_val, sum_sdv18, sum_sdv17, r_book, rel_diff, vis_elem_count_18
        ))
        
    term_rec = sample_records[-1]
    
    print("\n==================================================================")
    print("TRUE TERMINAL ODB STATE (Step-2 Frame 5000 at u = %.6f mm):" % term_rec['disp_u_mm'])
    print("  Unique Visualization Elements: %d" % term_rec['n_unique_vis_elements'])
    print("  Terminal E_elas:               %.8e kN*mm" % term_rec['E_elas_kN_mm'])
    print("  Terminal E_frac:               %.8e kN*mm" % term_rec['E_frac_kN_mm'])
    print("  Terminal E_elas + E_frac:      %.8e kN*mm" % (term_rec['E_elas_kN_mm'] + term_rec['E_frac_kN_mm']))
    print("  Terminal W_left:               %.8e kN*mm" % w_left)
    print("  Terminal W_trap:               %.8e kN*mm" % w_ext_trap)
    print("  Terminal W_right:              %.8e kN*mm" % w_right)
    print("  Terminal R_bookkeeping:        %.8e kN*mm" % term_rec['R_bookkeeping_kN_mm'])
    print("  Normalized R_bookkeeping:      %.4f %%" % term_rec['rel_diff_pct'])
    print("==================================================================")
    
    out_dict = {
        'provenance': {
            'pbs_job_id': '1406839.mmaster02',
            'odb_path': odb_path,
            'n_elements': total_elements,
            'n_nodes': total_nodes,
            'n_vis_elements': term_rec['n_unique_vis_elements'],
            'total_frames': total_pts
        },
        'terminal_state_u010': {
            'disp_u_mm': term_rec['disp_u_mm'],
            'force_RF2_kN': term_rec['force_RF2_RP_kN'],
            'W_left_kN_mm': w_left,
            'W_trap_kN_mm': w_ext_trap,
            'W_right_kN_mm': w_right,
            'E_elas_kN_mm': term_rec['E_elas_kN_mm'],
            'E_frac_kN_mm': term_rec['E_frac_kN_mm'],
            'E_tot_kN_mm': term_rec['E_elas_kN_mm'] + term_rec['E_frac_kN_mm'],
            'R_bookkeeping_kN_mm': term_rec['R_bookkeeping_kN_mm'],
            'R_bookkeeping_normalized_pct': term_rec['rel_diff_pct']
        },
        'sample_records': sample_records
    }
    
    with open(out_json, 'w') as f:
        json.dump(out_dict, f, indent=2)
    print("Saved true terminal ODB state to: " + str(out_json))
    
    odb.close()

if __name__ == '__main__':
    run()
