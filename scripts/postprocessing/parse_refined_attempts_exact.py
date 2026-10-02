#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse Exact Attempts for Step 3 in 1391300.mmaster02
"""

import os
import sys
import re
import json

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    msg_path = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.msg")
    
    with open(msg_path, "r") as f:
        lines = f.readlines()
        
    in_step3 = False
    curr_inc = None
    curr_att = None
    
    inc3_attempts = []
    all_step3_attempts = []
    
    for i, line in enumerate(lines):
        if "STEP    3" in line:
            in_step3 = True
        if in_step3 and "STEP    4" in line:
            in_step3 = False
            
        if in_step3:
            m_start = re.search(r"INCREMENT\s+(\d+)\s+STARTS\.\s+ATTEMPT NUMBER\s+(\d+),\s+TIME INCREMENT\s+([\d\.\+E\-]+)", line)
            if m_start:
                if curr_att is not None:
                    all_step3_attempts.append(curr_att)
                    if curr_inc == 3:
                        inc3_attempts.append(curr_att)
                        
                curr_inc = int(m_start.group(1))
                curr_att = {
                    "step": 3,
                    "inc_num": curr_inc,
                    "attempt_num": int(m_start.group(2)),
                    "dt_trial": float(m_start.group(3)),
                    "iterations": 0,
                    "divergence_reason": "Converged",
                    "hotspot_node": None,
                    "hotspot_dof": None,
                    "max_residual": None,
                    "max_disp_corr": None
                }
            elif curr_att is not None:
                if "EQUILIBRIUM ITERATION" in line:
                    curr_att["iterations"] += 1
                if "THE SOLUTION APPEARS TO BE DIVERGING" in line or "TIME INCREMENT WILL BE CUT BACK" in line or "FORCE EQUILIBRIUM NOT ACHIEVED" in line:
                    curr_att["divergence_reason"] = line.strip()
                m_node = re.search(r"AT NODE\s+(\d+)\s+DOF\s+(\d+)", line)
                if m_node and curr_att["hotspot_node"] is None:
                    curr_att["hotspot_node"] = int(m_node.group(1))
                    curr_att["hotspot_dof"] = int(m_node.group(2))
                if "LARGEST SCALED RESIDUAL FORCE" in line:
                    m_val = re.search(r"LARGEST SCALED RESIDUAL FORCE\s+([\d\.\+E\-]+)", line)
                    if m_val: curr_att["max_residual"] = float(m_val.group(1))
                if "LARGEST CORRECTION TO DISP." in line:
                    m_val = re.search(r"LARGEST CORRECTION TO DISP.\s+([\d\.\+E\-]+)", line)
                    if m_val: curr_att["max_disp_corr"] = float(m_val.group(1))
                    
        if "TOO MANY ATTEMPTS MADE" in line:
            if curr_att is not None:
                all_step3_attempts.append(curr_att)
                if curr_inc == 3:
                    inc3_attempts.append(curr_att)
            break
            
    print("================================================================================")
    print("STEP 3 INCREMENT 3 ATTEMPT-BY-ATTEMPT FORENSIC AUDIT (1391300.mmaster02):")
    print("================================================================================")
    print("Total Step 3 Inc 3 Attempts: %d" % len(inc3_attempts))
    
    for att in inc3_attempts:
        cutback_factor = 0.25 if "DIVERGING" in att["divergence_reason"] or att["attempt_num"] > 1 else 0.5
        next_req_dt = att["dt_trial"] * cutback_factor
        print("Attempt %2d: dt = %12.5e s | Iters = %2d | Hotspot Node %5s (DOF %s) | Max Res = %10.3e | Reason: %s" % (
            att["attempt_num"], att["dt_trial"], att["iterations"],
            str(att["hotspot_node"]), str(att["hotspot_dof"]),
            att["max_residual"] if att["max_residual"] is not None else 0.0,
            att["divergence_reason"]
        ))
        
    out_json = os.path.join(base_dir, "step3_inc3_exact_attempts.json")
    with open(out_json, "w") as fp:
        json.dump(inc3_attempts, fp, indent=2)
    print("\nSaved JSON to: %s" % out_json)

if __name__ == "__main__":
    main()
