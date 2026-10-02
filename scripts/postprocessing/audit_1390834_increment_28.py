#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Attempt-by-attempt Reconstruction and Forensic Audit of Increment 28
Job: 1390834.mmaster02 (M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL)
"""

import os
import sys
import json
import re

def audit_increment_28():
    msg_path = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.msg"
    sta_path = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.sta"
    
    with open(msg_path, "r") as f:
        msg_lines = f.readlines()
        
    with open(sta_path, "r") as f:
        sta_lines = f.readlines()
        
    print("=== STA FILE LINES FOR INCREMENT 28 ===")
    for line in sta_lines:
        if " 28 " in line or " 28U" in line:
            print(line.rstrip())
            
    print("\n=== ATTEMPT-BY-ATTEMPT PARSING OF INCREMENT 28 ===")
    inc28_lines = []
    capture = False
    for line in msg_lines:
        if "INCREMENT    28" in line or "INCREMENT   28" in line:
            capture = True
        if capture:
            inc28_lines.append(line)
            
    inc28_text = "".join(inc28_lines)
    
    # Split by attempt
    attempts = re.split(r"(INCREMENT\s+28\s+ATTEMPT NUMBER\s+\d+\s+.*)", inc28_text)
    
    parsed_attempts = []
    
    # Analyze each attempt
    for i in range(1, len(attempts), 2):
        header = attempts[i].strip()
        body = attempts[i+1]
        
        # Extract attempt number
        m_att = re.search(r"ATTEMPT NUMBER\s+(\d+)", header)
        att_num = int(m_att.group(1)) if m_att else -1
        
        # Extract time increment
        m_dt = re.search(r"TIME INCREMENT IS\s+([\d\.E\+\-]+)", header)
        dt_val = float(m_dt.group(1)) if m_dt else 0.0
        
        # Iteration count
        iter_matches = re.findall(r"ITERATION NUMBER\s+(\d+)", body)
        num_iters = len(iter_matches)
        
        # Residuals
        res_matches = re.findall(r"AVERAGE FORCE\s+([\d\.E\+\-]+)\s+LARGEST RESIDUAL FORCE\s+([\d\.E\+\-]+)\s+AT NODE\s+(\d+)\s+DOF\s+(\d+)", body)
        
        # Divergence / cutback reason
        reasons = []
        if "SOLUTION APPEARS TO BE DIVERGING" in body:
            reasons.append("SOLUTION APPEARS TO BE DIVERGING")
        if "TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED" in body:
            reasons.append("TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED")
        if "FORCE EQUILIBRIUM NOT ACHIEVED WITHIN ALLOWED NUMBER OF ITERATIONS" in body:
            reasons.append("FORCE EQUILIBRIUM NOT ACHIEVED (MAX ITERATIONS REACHED)")
            
        parsed_attempts.append({
            "attempt": att_num,
            "dt": dt_val,
            "num_iterations": num_iters,
            "iterations": iter_matches,
            "residuals": res_matches,
            "reasons": reasons,
            "body_snippet": body[:500]
        })
        
        print("\n--------------------------------------------------------------------------------")
        print("ATTEMPT %d: dt = %.6e s, Iterations = %d" % (att_num, dt_val, num_iters))
        print("Header: %s" % header)
        if reasons:
            print("Cutback / Termination Reason: %s" % "; ".join(reasons))
        if res_matches:
            last_res = res_matches[-1]
            print("Last Iteration Residual: Avg Force = %s, Max Res = %s at Node %s DOF %s" % (
                last_res[0], last_res[1], last_res[2], last_res[3]))
                
    # Check cutback factors:
    print("\n================================================================================")
    print("CUTBACK FACTOR SEQUENCE:")
    print("================================================================================")
    for idx in range(len(parsed_attempts)-1):
        dt_curr = parsed_attempts[idx]["dt"]
        dt_next = parsed_attempts[idx+1]["dt"]
        factor = dt_next / dt_curr
        print("Cutback %2d -> %2d: dt_curr = %.6e -> dt_next = %.6e (Factor = %.4f)" % (
            parsed_attempts[idx]["attempt"], parsed_attempts[idx+1]["attempt"], dt_curr, dt_next, factor))

if __name__ == "__main__":
    audit_increment_28()
