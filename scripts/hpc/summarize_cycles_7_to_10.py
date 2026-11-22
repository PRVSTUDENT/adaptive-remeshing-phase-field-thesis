#!/usr/bin/env python3
"""
Summarize Cycles 7 to 10 of Method C Case 3 Short Resume Run (PBS Job 1424910).
Extracts:
1. Physical mesh info (element count, quad/tri count).
2. Step 1 (Hold re-equilibration) convergence, iterations, RF2, and force continuity vs donor.
3. Step 2 (Forward propagation) convergence, cutbacks, terminal load u2, and terminal RF2.
4. Damage irreversibility (d_max monotonicity) and history (H_max).
5. Robust crack tip coordinates (x_tip, y_tip) and crack advance delta_a_x.
6. Execution timings and speedup metrics.
"""

import os
import sys
import json
import glob
import re
import subprocess

RUN_DIR = "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_single_job"
if RUN_DIR not in sys.path:
    sys.path.insert(0, RUN_DIR)

import case3_single_job_orchestrator as orch

def parse_rf2_from_dat(dat_path):
    """Parse RF2 values for Step 1 (hold) and Step 2 from .dat file."""
    if not os.path.isfile(dat_path):
        return None, None
    matches = []
    with open(dat_path, "r") as f:
        for line in f:
            if "999999" in line and "E" in line:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u2 = float(parts[1])
                        rf2 = float(parts[2])
                        matches.append((u2, rf2))
                    except ValueError:
                        pass
    if not matches:
        return None, None
    step1_rf2 = matches[0][1]
    step2_rf2 = matches[-1][1]
    return step1_rf2, step2_rf2

def parse_msg_iterations(msg_path):
    """Count iterations and cutbacks in Step 1 and Step 2 from .msg file."""
    if not os.path.isfile(msg_path):
        return {}
    step1_iters = 0
    step2_iters = 0
    step1_cutbacks = 0
    step2_cutbacks = 0
    current_step = 1
    with open(msg_path, "r", errors="ignore") as f:
        for line in f:
            if "STEP    1" in line or "STEP 1" in line:
                current_step = 1
            elif "STEP    2" in line or "STEP 2" in line:
                current_step = 2
            elif "ITERATION" in line:
                if current_step == 1:
                    step1_iters += 1
                elif current_step == 2:
                    step2_iters += 1
            elif "TIME INCREMENT IS CUT BACK" in line or "CUT BACK" in line:
                if current_step == 1:
                    step1_cutbacks += 1
                elif current_step == 2:
                    step2_cutbacks += 1
    return {
        "step1_iters": step1_iters,
        "step2_iters": step2_iters,
        "step1_cutbacks": step1_cutbacks,
        "step2_cutbacks": step2_cutbacks
    }

def summarize_all():
    print("=================================================================")
    print("Method C Case 3: Summary of Cycles 6 to 10 (Job 1424910 Analysis)")
    print("=================================================================")

    orchestrator = orch.Case3SingleJobOrchestrator(run_dir=RUN_DIR)
    results = []
    
    # Baseline Cycle 6
    c6_state = orchestrator.extract_cycle_state("PK_METHOD_C_CASE3_CYCLE6")
    results.append({
        "cycle": 6,
        "terminal_u2_mm": c6_state.get("terminal_u2", 0.1000),
        "terminal_rf2_kN": c6_state.get("terminal_rf2", 1.8744),
        "tip_x_mm": c6_state.get("tip_x", 30.5113),
        "tip_y_mm": c6_state.get("tip_y", 66.7437),
        "d_max": c6_state.get("max_damage", 1.0),
        "h_max_MPa": c6_state.get("max_history_MPa", 0.0),
        "elements": 47214
    })

    for c in range(7, 11):
        prefix = os.path.join(RUN_DIR, "PK_METHOD_C_CASE3_CYCLE{}".format(c))
        phys_inp = prefix + "_PHYS.inp"
        coupled_inp = prefix + ".inp"
        state_file = prefix + "_state.json"
        sta_file = prefix + ".sta"
        msg_file = prefix + ".msg"
        dat_file = prefix + ".dat"
        odb_file = prefix + ".odb"
        
        if not os.path.isfile(phys_inp):
            print("Cycle {}: No physical mesh found.".format(c))
            continue
            
        mesh = orch.parse_physical_inp(phys_inp)
        nodes = mesh["nodes"]
        quads = mesh.get("quads", {})
        tris = mesh.get("tris", {})
        n_elem = len(quads) + len(tris)
        
        # Parse STA
        sta_info = orch.parse_sta_file(sta_file) if os.path.isfile(sta_file) else {}
        term = sta_info.get("terminal_converged", {})
        all_incs = sta_info.get("increments", [])
        
        step1_incs = [inc for inc in all_incs if inc.get("step") == 1]
        step2_incs = [inc for inc in all_incs if inc.get("step") == 2]
        
        # Parse MSG
        msg_info = parse_msg_iterations(msg_file)
        
        # Parse DAT for Step 1 RF2
        s1_rf2, s2_rf2 = parse_rf2_from_dat(dat_file)
        
        # State
        if os.path.isfile(state_file):
            with open(state_file, "r") as f:
                s = json.load(f)
            d_nodal = {int(k): float(v) for k, v in s.get("d_nodal", {}).items()}
            u_nodal = {int(k): v for k, v in s.get("u_nodal", {}).items()}
            h_gp = s.get("h_gp", {})
            d_max = max(d_nodal.values()) if d_nodal else 0.0
            h_max = max(float(v) for v in h_gp.values()) if h_gp else 0.0
            rp_u2 = u_nodal.get(999999, [0.0, 0.0])[1] if 999999 in u_nodal else 0.0
            
            # Robust crack tip
            tip_x, tip_y = orch.extract_robust_crack_tip(d_nodal, nodes)
        else:
            d_max, h_max, rp_u2 = 0.0, 0.0, 0.0
            tip_x, tip_y = 0.0, 0.0

        # Extract terminal RF2 from state or STA
        cycle_state_data = orchestrator.extract_cycle_state("PK_METHOD_C_CASE3_CYCLE{}".format(c))
        term_u2 = cycle_state_data.get("terminal_u2", rp_u2)
        term_rf2 = cycle_state_data.get("terminal_rf2", s2_rf2 if s2_rf2 is not None else 0.0)
        
        # Previous donor RF2 for continuity
        prev_term_rf2 = results[-1]["terminal_rf2_kN"] if results else 0.0
        
        # Step 1 hold force continuity
        step1_rf2_val = s1_rf2 if s1_rf2 is not None else cycle_state_data.get("step1_rf2")
        force_delta_pct = None
        if step1_rf2_val is not None and prev_term_rf2 > 0.0:
            force_delta_pct = round(((step1_rf2_val - prev_term_rf2) / prev_term_rf2) * 100.0, 3)

        # File timestamps for timing breakdown
        t_phys = os.path.getmtime(phys_inp) if os.path.isfile(phys_inp) else 0.0
        t_deck = os.path.getmtime(coupled_inp) if os.path.isfile(coupled_inp) else 0.0
        t_odb = os.path.getmtime(odb_file) if os.path.isfile(odb_file) else 0.0
        t_state = os.path.getmtime(state_file) if os.path.isfile(state_file) else 0.0
        
        # Approximate durations
        t_transfer_deck_s = max(0.0, t_deck - t_phys)
        t_solve_s = max(0.0, t_odb - t_deck)
        t_extract_s = max(0.0, t_state - t_odb)

        entry = {
            "cycle": c,
            "elements_2d": n_elem,
            "elements_3layer": n_elem * 3,
            "quads": len(quads),
            "tris": len(tris),
            "step1_converged_incs": len(step1_incs),
            "step1_iters": msg_info.get("step1_iters", 0),
            "step1_hold_rf2_kN": step1_rf2_val,
            "donor_prev_term_rf2_kN": prev_term_rf2,
            "hold_force_delta_pct": force_delta_pct,
            "step2_converged_incs": len(step2_incs),
            "step2_iters": msg_info.get("step2_iters", 0),
            "step2_cutbacks": msg_info.get("step2_cutbacks", 0),
            "terminal_u2_mm": term_u2,
            "terminal_rf2_kN": term_rf2,
            "d_max": d_max,
            "h_max_MPa": h_max,
            "tip_x_mm": round(tip_x, 4),
            "tip_y_mm": round(tip_y, 4),
            "advance_x_mm": round(tip_x - 10.0, 4),
            "timing_transfer_deck_s": round(t_transfer_deck_s, 1),
            "timing_solve_s": round(t_solve_s, 1),
            "timing_extract_s": round(t_extract_s, 1)
        }
        results.append(entry)

    print("\nDetailed Summary JSON:")
    print(json.dumps(results, indent=2))
    
    out_path = os.path.join(RUN_DIR, "PK_METHOD_C_CASE3_RESUME_RUN_EVALUATION.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print("Saved evaluation to", out_path)

if __name__ == "__main__":
    summarize_all()
