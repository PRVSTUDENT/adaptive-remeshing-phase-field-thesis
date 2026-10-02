#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abaqus Python Scientific Evaluation Script for Stage-D Corrected Nonmatching Transfer Job.
Compares M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL against native H1 (1389686.mmaster02).
"""

import sys
import os
import json
import math
from odbAccess import openOdb

def evaluate():
    h1_odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    staged_odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    
    print("================================================================================")
    print("STAGE-D CORRECTED SOLVER-LEVEL SCIENTIFIC EVALUATION")
    print("================================================================================")
    
    odb_h1 = openOdb(h1_odb_path, readOnly=True)
    odb_sd = openOdb(staged_odb_path, readOnly=True)
    
    # -------------------------------------------------------------------------
    # 1. Native H1 Source Handoff State (Frame 29)
    # -------------------------------------------------------------------------
    h1_step = odb_h1.steps['ShearStep']
    h1_frame29 = h1_step.frames[29]
    h1_u_field = h1_frame29.fieldOutputs['U']
    h1_rf_field = h1_frame29.fieldOutputs['RF']
    
    # Extract RP RF1 in H1
    h1_rf1_tot = 0.0
    for val in h1_rf_field.values:
        if abs(val.data[0]) > 1.0e-8:
            h1_rf1_tot += val.data[0]
            
    # Also get RF1 from history if available
    h1_rf1_hist = []
    h1_u1_hist = []
    try:
        for key in odb_h1.steps['ShearStep'].historyRegions.keys():
            hr = odb_h1.steps['ShearStep'].historyRegions[key]
            if 'RF1' in hr.historyOutputs:
                h1_rf1_hist = [pt[1] for pt in hr.historyOutputs['RF1'].data]
            if 'U1' in hr.historyOutputs:
                h1_u1_hist = [pt[1] for pt in hr.historyOutputs['U1'].data]
    except Exception as e:
        print("H1 history error: %s" % e)
        
    print("Native H1 Frame 29: RF1 field sum = %.6f kN" % h1_rf1_tot)
    if h1_rf1_hist:
        print("Native H1 Frame 29: RF1 history = %.6f kN at U1 = %.6f mm" % (h1_rf1_hist[29], h1_u1_hist[29]))
        
    # -------------------------------------------------------------------------
    # 2. Stage-D Steps Tracking
    # -------------------------------------------------------------------------
    step_names = list(odb_sd.steps.keys())
    print("\nStage-D Steps present: %s" % step_names)
    
    results = {}
    
    # Check max d across all steps and frames
    phase_history_nodes = {}
    max_d_by_step = {}
    
    for s_name in step_names:
        step = odb_sd.steps[s_name]
        n_frames = len(step.frames)
        max_d_list = []
        rf1_list = []
        u1_list = []
        
        for f_idx, frame in enumerate(step.frames):
            u_field = frame.fieldOutputs['U'] if 'U' in frame.fieldOutputs else None
            rf_field = frame.fieldOutputs['RF'] if 'RF' in frame.fieldOutputs else None
            
            d_max_frame = 0.0
            if u_field:
                for val in u_field.values:
                    if len(val.data) >= 3:
                        d_val = val.data[2] # U3 is phase field
                        if d_val > d_max_frame:
                            d_max_frame = d_val
                        # Track central crack-tip nodes
                        nid = val.nodeLabel
                        if nid not in phase_history_nodes:
                            phase_history_nodes[nid] = []
                        phase_history_nodes[nid].append((s_name, f_idx, d_val))
            max_d_list.append(d_max_frame)
            
            rf_tot = 0.0
            if rf_field:
                for val in rf_field.values:
                    if abs(val.data[0]) > 1.0e-8:
                        rf_tot += val.data[0]
            rf1_list.append(rf_tot)
            
        max_d_by_step[s_name] = {
            'frames': n_frames,
            'd_max_initial': max_d_list[0] if max_d_list else 0.0,
            'd_max_final': max_d_list[-1] if max_d_list else 0.0,
            'rf1_final': rf1_list[-1] if rf1_list else 0.0
        }
        print("  Step %s (%d frames): d_max = [%.6f -> %.6f], RF1_final = %.6f kN" % (
            s_name, n_frames, max_d_list[0] if max_d_list else 0.0, max_d_list[-1] if max_d_list else 0.0, rf1_list[-1] if rf1_list else 0.0))

    # -------------------------------------------------------------------------
    # 3. Pointwise Irreversibility Audit (min Delta d across every frame)
    # -------------------------------------------------------------------------
    min_delta_d_global = 0.0
    healing_violations = 0
    
    for nid, d_trace in phase_history_nodes.items():
        for i in range(1, len(d_trace)):
            s_prev, f_prev, d_prev = d_trace[i-1]
            s_curr, f_curr, d_curr = d_trace[i]
            delta = d_curr - d_prev
            if delta < min_delta_d_global:
                min_delta_d_global = delta
            if delta < -1.0e-6:
                healing_violations += 1
                if healing_violations <= 5:
                    print("  [HEALING DETECTED] Node %d: %s f%d (%.6f) -> %s f%d (%.6f), delta = %+.6e" % (
                        nid, s_prev, f_prev, d_prev, s_curr, f_curr, d_curr, delta))
                    
    print("\n--- POINTWISE IRREVERSIBILITY SUMMARY ---")
    print("  Global min(Delta d): %+.6e" % min_delta_d_global)
    print("  Total Healing Violations (Delta d < -1e-6): %d" % healing_violations)
    if min_delta_d_global >= -1.0e-6:
        print("  R7 IRREVERSIBILITY CRITERION: PASSED (min Delta d >= -1e-6)")
    else:
        print("  R7 IRREVERSIBILITY CRITERION: FAILED")

    # -------------------------------------------------------------------------
    # 4. Continuation Step Load-Displacement & Softening Response
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # 4. Continuation Step Load-Displacement & Softening Response
    # -------------------------------------------------------------------------
    cont_step = odb_sd.steps['CONTINUATION'] if 'CONTINUATION' in odb_sd.steps else None
    if cont_step:
        cont_frames = len(cont_step.frames)
        d_max_cont_final = 0.0
        last_frame = cont_step.frames[-1]
        if 'U' in last_frame.fieldOutputs:
            for val in last_frame.fieldOutputs['U'].values:
                if len(val.data) >= 3 and val.data[2] > d_max_cont_final:
                    d_max_cont_final = val.data[2]
        print("\n--- CONTINUATION STEP SUMMARY ---")
        print("  Total Converged Increments in Continuation: %d" % (cont_frames - 1))
        print("  Final Phase Field Peak (d_max): %.6f" % d_max_cont_final)
        
    # Extract History Curves for Stage-D
    sd_rf1_hist = []
    sd_u1_hist = []
    try:
        if 'CONTINUATION' in odb_sd.steps:
            hr_dict = odb_sd.steps['CONTINUATION'].historyRegions
            for key in hr_dict.keys():
                hr = hr_dict[key]
                if 'RF1' in hr.historyOutputs and len(hr.historyOutputs['RF1'].data) > 0:
                    sd_rf1_hist = [pt[1] for pt in hr.historyOutputs['RF1'].data]
                if 'U1' in hr.historyOutputs and len(hr.historyOutputs['U1'].data) > 0:
                    sd_u1_hist = [pt[1] for pt in hr.historyOutputs['U1'].data]
    except Exception as e:
        print("Stage-D history error: %s" % e)

    print("\n--- LOAD-DISPLACEMENT CONTINUATION ANALYSIS ---")
    if sd_rf1_hist:
        max_rf1_sd = max(sd_rf1_hist)
        idx_peak = sd_rf1_hist.index(max_rf1_sd)
        u1_peak = sd_u1_hist[idx_peak]
        print("  Stage-D Peak Load: RF1_max = %.6f kN at U1 = %.6f mm" % (max_rf1_sd, u1_peak))
        print("  Stage-D Final Load: RF1_final = %.6f kN at U1 = %.6f mm" % (sd_rf1_hist[-1], sd_u1_hist[-1]))
    
    if h1_rf1_hist:
        max_rf1_h1 = max(h1_rf1_hist)
        idx_peak_h1 = h1_rf1_hist.index(max_rf1_h1)
        u1_peak_h1 = h1_u1_hist[idx_peak_h1]
        print("  Native H1 Peak Load: RF1_max = %.6f kN at U1 = %.6f mm" % (max_rf1_h1, u1_peak_h1))
        print("  Native H1 Final Load: RF1_final = %.6f kN at U1 = %.6f mm" % (h1_rf1_hist[-1], h1_u1_hist[-1]))
        if sd_rf1_hist:
            diff_peak_rf = (max_rf1_sd - max_rf1_h1) / max_rf1_h1 * 100.0
            print("  Peak Load Parity Difference: %+.2f%%" % diff_peak_rf)
        
    odb_h1.close()
    odb_sd.close()
    
    return {
        'h1_rf1_handoff': h1_rf1_tot,
        'max_d_by_step': max_d_by_step,
        'min_delta_d_global': min_delta_d_global,
        'healing_violations': healing_violations
    }

if __name__ == "__main__":
    evaluate()
