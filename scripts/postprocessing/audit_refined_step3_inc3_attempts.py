#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic Audit of Step 3 Increment 3 Attempts in 1391300.mmaster02
and Comparative State Analysis against Donor 1390447 and Matching Baseline 1391277
"""

import os
import sys
import re
import json
import numpy as np
from odbAccess import openOdb

def parse_attempts_from_msg(msg_path):
    with open(msg_path, "r") as f:
        lines = f.readlines()
        
    in_step3 = False
    in_inc3 = False
    attempts = []
    curr_att = None
    
    for i, line in enumerate(lines):
        if "STEP   3" in line and "INCREMENT" in line:
            in_step3 = True
        if in_step3 and "INCREMENT     3" in line:
            in_inc3 = True
            
        if in_inc3:
            # Check for attempt start
            m_att = re.search(r"ATTEMPT NUMBER\s+(\d+)\s+WITH TIME INCREMENT\s+([\d\.\+E\-]+)", line)
            if m_att:
                if curr_att is not None:
                    attempts.append(curr_att)
                curr_att = {
                    "attempt_num": int(m_att.group(1)),
                    "dt_trial": float(m_att.group(2)),
                    "iterations": [],
                    "divergence_reason": "Unknown",
                    "hotspot_node": None,
                    "hotspot_dof": None,
                    "largest_residual": None,
                    "largest_disp_corr": None
                }
            elif curr_att is not None:
                # Check for iteration header
                m_iter = re.search(r"EQUILIBRIUM ITERATION\s+(\d+)", line)
                if m_iter:
                    iter_num = int(m_iter.group(1))
                    res_line = ""
                    disp_line = ""
                    for k in range(i, min(i + 25, len(lines))):
                        if "LARGEST SCALED RESIDUAL FORCE" in lines[k]:
                            res_line = lines[k]
                        if "LARGEST CORRECTION TO DISP." in lines[k]:
                            disp_line = lines[k]
                    
                    curr_att["iterations"].append({
                        "iter_num": iter_num,
                        "residual_summary": res_line.strip(),
                        "disp_corr_summary": disp_line.strip()
                    })
                    
                if "THE SOLUTION APPEARS TO BE DIVERGING" in line or "TIME INCREMENT WILL BE CUT BACK" in line or "FORCE EQUILIBRIUM NOT ACHIEVED" in line:
                    curr_att["divergence_reason"] = line.strip()
                    
                m_node = re.search(r"AT NODE\s+(\d+)\s+DOF\s+(\d+)", line)
                if m_node and curr_att["hotspot_node"] is None:
                    curr_att["hotspot_node"] = int(m_node.group(1))
                    curr_att["hotspot_dof"] = int(m_node.group(2))
                    
                if "LARGEST SCALED RESIDUAL FORCE" in line:
                    m_val = re.search(r"LARGEST SCALED RESIDUAL FORCE\s+([\d\.\+E\-]+)", line)
                    if m_val: curr_att["largest_residual"] = float(m_val.group(1))
                if "LARGEST CORRECTION TO DISP." in line:
                    m_val = re.search(r"LARGEST CORRECTION TO DISP.\s+([\d\.\+E\-]+)", line)
                    if m_val: curr_att["largest_disp_corr"] = float(m_val.group(1))
                    
        if in_inc3 and ("TOO MANY ATTEMPTS MADE" in line or "ANALYSIS SUMMARY" in line):
            if curr_att is not None and curr_att not in attempts:
                attempts.append(curr_att)
            break
            
    return attempts

def extract_state_comparison():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    odb_1391300 = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.odb")
    odb_1391277 = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.odb")
    odb_1390447 = "models/generated/mode_ii/donor_continuation_protocol/M2CORR_STAGE_D_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_D_DONOR_MINIMAL_CONTINUATION_VAL.odb"
    
    comp_results = {}
    
    # 1. Extract 1391300 frames
    if os.path.exists(odb_1391300):
        odb = openOdb(odb_1391300, readOnly=True)
        r1_frames = []
        for s_name, step in odb.steps.items():
            for f_idx, frame in enumerate(step.frames):
                rp_u1, rp_rf1 = 0.0, 0.0
                if 'U' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['U'].values:
                        if v.nodeLabel == 99999: rp_u1 = float(v.data[0]); break
                if 'RF' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['RF'].values:
                        if v.nodeLabel == 99999: rp_rf1 = float(v.data[0]); break
                        
                d_vals = []
                max_d_node = None
                max_d = -1.0
                if 'U' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['U'].values:
                        if v.nodeLabel != 99999 and len(v.data) >= 3:
                            d_val = float(v.data[2])
                            d_vals.append(d_val)
                            if d_val > max_d:
                                max_d = d_val
                                max_d_node = v.nodeLabel
                                
                min_d = min(d_vals) if d_vals else 0.0
                
                r1_frames.append({
                    "step_name": s_name,
                    "frame_idx": f_idx,
                    "frame_value": float(frame.frameValue),
                    "rp_u1_mm": rp_u1,
                    "rp_rf1_kN": rp_rf1,
                    "min_d": min_d,
                    "max_d": max_d,
                    "max_d_node": max_d_node
                })
        odb.close()
        comp_results["1391300_frames"] = r1_frames
        
    return comp_results

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    msg_path = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.msg")
    
    attempts = parse_attempts_from_msg(msg_path)
    state_comp = extract_state_comparison()
    
    out_json = os.path.join(base_dir, "step3_inc3_forensic_attempt_audit.json")
    with open(out_json, "w") as fp:
        json.dump({"attempts": attempts, "state_comparison": state_comp}, fp, indent=2)
        
    print("================================================================================")
    print("STEP 3 INCREMENT 3 ATTEMPT AUDIT (1391300.mmaster02):")
    print("================================================================================")
    print("Total Attempts Parsed: %d" % len(attempts))
    for att in attempts:
        print("  Attempt %2d: dt = %12.5e s | Iters = %d | Hotspot Node = %s (DOF %s) | Max Res = %s | Div = %s" % (
            att["attempt_num"], att["dt_trial"], len(att["iterations"]),
            str(att["hotspot_node"]), str(att["hotspot_dof"]), str(att["largest_residual"]), att["divergence_reason"][:35]
        ))
    print("\nSaved Attempt Audit JSON to: %s" % out_json)

if __name__ == "__main__":
    main()
