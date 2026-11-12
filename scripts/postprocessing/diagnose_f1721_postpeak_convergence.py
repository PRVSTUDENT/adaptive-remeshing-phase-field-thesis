"""
Diagnose F1720 Post-Peak Nonlinear Convergence Failure
Inspects MSG, STA, CSV curves, and telemetry to evaluate the four competing hypotheses:
A. Constitutive tangent inconsistency
B. Phase-field coupling and history evolution
C. Structural snap-through / snap-back instability
D. Numerical implementation / constraint defects
"""

import os
import re
import sys
import json
import numpy as np

def run_diagnostics():
    base_dir = "models/pandey_kumar_mode1/214_f1720_adapted_mesh"
    msg_path = os.path.join(base_dir, "PK_F1720_ADAPTED_PFM.msg")
    sta_path = os.path.join(base_dir, "PK_F1720_ADAPTED_PFM.sta")
    inp_path = os.path.join(base_dir, "PK_F1720_ADAPTED_PFM.inp")
    curves_path = "results/validation/f1720_adapted_pfm_curves.csv"
    
    print("=" * 80)
    print("F1721 POST-PEAK NONLINEAR CONVERGENCE DIAGNOSIS")
    print("=" * 80)
    
    # 1. Parse Node Coordinates of Key Nodes
    key_nodes = {}
    with open(inp_path, "r") as f:
        for line in f:
            if line.startswith("*ELEMENT"):
                break
            if not line.startswith("*"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        key_nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
    
    print(f"Total nodes indexed from INP: {len(key_nodes)}")
    
    # 2. Parse STA File
    # Format of STA:
    # STEP INC ATT SEVERE EQUIL TOTAL  TOTAL      STEP       INC OF     TOTAL
    #                  DISCON ITERS ITERS TIME/FREQ  TIME/LPF   TIME/LPF   TIME/LPF
    sta_records = []
    with open(sta_path, "r") as f:
        for line in f:
            line = line.strip()
            # Look for lines starting with integer step
            parts = line.split()
            if len(parts) >= 9:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att = int(parts[2])
                    eq_iters = int(parts[4])
                    tot_iters = int(parts[5])
                    tot_time = float(parts[6])
                    step_time = float(parts[7])
                    inc_time = float(parts[8])
                    sta_records.append({
                        "step": step, "inc": inc, "att": att,
                        "eq_iters": eq_iters, "tot_iters": tot_iters,
                        "tot_time": tot_time, "step_time": step_time,
                        "inc_time": inc_time
                    })
                except ValueError:
                    pass
    
    print(f"Total STA records parsed: {len(sta_records)}")
    if sta_records:
        step2_recs = [r for r in sta_records if r["step"] == 2]
        print(f"Step 1 records: {len(sta_records) - len(step2_recs)}, Step 2 records: {len(step2_recs)}")
        print(f"Final STA record: Step {sta_records[-1]['step']}, Inc {sta_records[-1]['inc']}, "
              f"Att {sta_records[-1]['att']}, dt={sta_records[-1]['inc_time']:.3e}, step_time={sta_records[-1]['step_time']:.6f}")
    
    # 3. Parse MSG File Convergence Telemetry
    with open(msg_path, "r") as f:
        msg_text = f.read()
    
    inc_blocks = re.findall(r'(INCREMENT\s+(\d+)\s+STARTS.*?)(?=INCREMENT\s+\d+\s+STARTS|\Z)', msg_text, re.DOTALL)
    print(f"Total increment blocks in MSG: {len(inc_blocks)}")
    
    recent_incs_data = []
    for inc_text, inc_num in inc_blocks[-15:]:
        inum = int(inc_num)
        attempts = re.findall(r'ATTEMPT NUMBER\s+(\d+),\s+TIME INCREMENT\s+([\d\.E\+\-]+)', inc_text)
        
        # Check equilibrium iterations
        iter_matches = re.finditer(
            r'CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION\s+(\d+).*?'
            r'AVERAGE FORCE\s+([\d\.E\+\-]+)\s+TIME AVG\. FORCE\s+([\d\.E\+\-]+).*?'
            r'LARGEST SCALED RESIDUAL FORCE\s+([\d\.E\+\-]+)\s+AT NODE\s+(\d+)\s+DOF\s+(\d+).*?'
            r'LARGEST INCREMENT OF DISP\.\s+([\d\.E\+\-]+)\s+AT NODE\s+(\d+)\s+DOF\s+(\d+).*?'
            r'LARGEST CORRECTION TO DISP\.\s+([\d\.E\+\-]+)\s+AT NODE\s+(\d+)\s+DOF\s+(\d+)',
            inc_text, re.DOTALL
        )
        
        iters_data = []
        for m in iter_matches:
            iters_data.append({
                "iteration": int(m.group(1)),
                "avg_force": float(m.group(2)),
                "time_avg_force": float(m.group(3)),
                "max_res": float(m.group(4)),
                "res_node": int(m.group(5)),
                "res_dof": int(m.group(6)),
                "max_disp_inc": float(m.group(7)),
                "disp_inc_node": int(m.group(8)),
                "disp_inc_dof": int(m.group(9)),
                "max_corr": float(m.group(10)),
                "corr_node": int(m.group(11)),
                "corr_dof": int(m.group(12)),
            })
            
        recent_incs_data.append({
            "inc_num": inum,
            "attempts": attempts,
            "iterations": iters_data,
            "has_divergence_note": "THE SOLUTION APPEARS TO BE DIVERGING" in inc_text,
            "has_severe_error": "***ERROR: TIME INCREMENT REQUIRED IS LESS THAN" in inc_text
        })
    
    print("\n--- RECENT INCREMENT CONVERGENCE SUMMARY ---")
    for d in recent_incs_data:
        att_str = ", ".join([f"Att {a[0]} (dt={float(a[1]):.1e})" for a in d["attempts"]])
        num_iters = len(d["iterations"])
        last_res = f"{d['iterations'][-1]['max_res']:.2e} (N{d['iterations'][-1]['res_node']} DOF{d['iterations'][-1]['res_dof']})" if d["iterations"] else "N/A"
        last_corr = f"{d['iterations'][-1]['max_corr']:.2e} (N{d['iterations'][-1]['corr_node']} DOF{d['iterations'][-1]['corr_dof']})" if d["iterations"] else "N/A"
        print(f"Inc {d['inc_num']:3d}: {len(d['attempts'])} attempts, {num_iters:2d} iters | Last Res: {last_res} | Last Corr: {last_corr} | Div: {d['has_divergence_note']}")
    
    # 4. Detailed Analysis of Increment 127
    inc127 = [d for d in recent_incs_data if d["inc_num"] == 127]
    if inc127:
        print("\n--- DETAILED ITERATION LOG FOR TERMINAL INCREMENT 127 ---")
        for it in inc127[0]["iterations"]:
            r_node = it["res_node"]
            r_coords = key_nodes.get(r_node, (0.0, 0.0))
            c_node = it["corr_node"]
            c_coords = key_nodes.get(c_node, (0.0, 0.0))
            print(f"Iter {it['iteration']:2d}: MaxRes = {it['max_res']:.3e} (Node {r_node:5d} @ ({r_coords[0]:.4f}, {r_coords[1]:.4f}) DOF {it['res_dof']}) | "
                  f"MaxCorr = {it['max_corr']:.3e} (Node {c_node:5d} @ ({c_coords[0]:.4f}, {c_coords[1]:.4f}) DOF {it['corr_dof']})")
    
    # 5. Load-Displacement & Tangent Stiffness Curve Analysis
    if os.path.exists(curves_path):
        import csv
        with open(curves_path, "r") as f:
            reader = csv.DictReader(f)
            curve_rows = list(reader)
        
        print(f"\n--- LOAD-DISPLACEMENT ANALYSIS (Curves rows: {len(curve_rows)}) ---")
        u_vals = [float(r["displacement_mm"]) for r in curve_rows]
        rf_vals = [float(r["force_kN"]) for r in curve_rows]
        d_vals = [float(r["max_damage"]) for r in curve_rows]
        d_lig3 = [float(r["max_damage_lig3"]) for r in curve_rows]
        
        # Find peak
        max_rf = -1.0
        max_idx = -1
        for i, rf in enumerate(rf_vals):
            if rf > max_rf:
                max_rf = rf
                max_idx = i
        
        print(f"Peak Force: F_max = {max_rf:.6f} kN at u = {u_vals[max_idx]:.7f} mm (point {max_idx})")
        print(f"Final Point: F_final = {rf_vals[-1]:.6f} kN at u = {u_vals[-1]:.7f} mm (point {len(rf_vals)-1})")
        
        # Post-peak softening behavior
        post_peak_u = u_vals[max_idx:]
        post_peak_f = rf_vals[max_idx:]
        print(f"Post-peak points: {len(post_peak_u)}")
        
        tangents = []
        for i in range(len(post_peak_u) - 1):
            du = post_peak_u[i+1] - post_peak_u[i]
            df = post_peak_f[i+1] - post_peak_f[i]
            if abs(du) > 1e-12:
                tangent = df / du
                tangents.append((post_peak_u[i+1], df, du, tangent))
        
        print("Last 15 post-peak increments:")
        for idx in range(len(post_peak_u) - 15, len(post_peak_u)):
            u = u_vals[max_idx + idx]
            f_val = rf_vals[max_idx + idx]
            d_glob = d_vals[max_idx + idx]
            d_l3 = d_lig3[max_idx + idx]
            if idx > 0:
                du = u_vals[max_idx + idx] - u_vals[max_idx + idx - 1]
                df = rf_vals[max_idx + idx] - rf_vals[max_idx + idx - 1]
                k_tan = df / du if abs(du) > 1e-12 else 0.0
            else:
                du, df, k_tan = 0.0, 0.0, 0.0
            print(f"  [{idx:2d}] u = {u:.7f} mm | F = {f_val:.6f} kN | du = {du:.2e} | df = {df:.2e} | dF/du = {k_tan:10.1f} kN/mm | d_max = {d_glob:.4f} | d_lig3 = {d_l3:.4f}")
            
        # Check monotonicity of displacement
        is_u_monotonic = all(post_peak_u[i+1] >= post_peak_u[i] for i in range(len(post_peak_u)-1))
        print(f"Is post-peak displacement strictly monotonic? {is_u_monotonic}")
        
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_diagnostics()
